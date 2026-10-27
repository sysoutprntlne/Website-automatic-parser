"""Authenticated loopback API. No delivery endpoint; Gmail controls sending."""

from hmac import compare_digest
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import secrets
import time

from src.config import Config, private_write
from src.domain import Record
from pydantic import Field


class MessageRequest(Record):
    message_id: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")


class GenerateRequest(MessageRequest):
    intent: str = Field(min_length=1, max_length=4000)


class QueueRequest(Record):
    refresh: bool = False
    page_token: str = Field(default="", max_length=1000)


class RejectedRequest(RuntimeError):
    def __init__(self, status, message):
        self.status, self.message = status, message


class Backend:
    def __init__(self, gmail, assistant, memory, token, config, demo=False):
        if len(token) < 32:
            raise ValueError("Backend token must have at least 32 characters")
        if config.extension_origin and not re.fullmatch(
            r"chrome-extension://[a-p]{32}", config.extension_origin
        ):
            raise ValueError("Configure the exact unpacked extension origin")
        self.gmail, self.assistant, self.memory = gmail, assistant, memory
        self.token, self.config, self.demo = token, config, demo
        from src.triage import ReplyQueue

        self.queue = ReplyQueue(gmail, config)
        self.confirmed = (
            {}
        )  # Short-lived association of selected thread, not draft content.

    def allowed_origin(self, origin):
        return origin == f"http://127.0.0.1:{self.config.port}" or bool(
            self.config.extension_origin and origin == self.config.extension_origin
        )

    def authorize(self, headers, preflight=False):
        if headers.get("Host") != f"127.0.0.1:{self.config.port}":
            raise RejectedRequest(403, "Invalid Host")
        origin = headers.get("Origin")
        if origin is not None and not self.allowed_origin(origin):
            raise RejectedRequest(403, "Origin rejected")
        if preflight:
            if not self.allowed_origin(origin):
                raise RejectedRequest(403, "Origin required")
        elif not compare_digest(
            headers.get("Authorization", ""), "Bearer " + self.token
        ):
            raise RejectedRequest(401, "Pairing token required")

    def dispatch(self, path, payload):
        if path == "/queue":
            args = QueueRequest.model_validate(payload)
            return dict(
                self.queue.scan(refresh=args.refresh, page_token=args.page_token),
                demo=self.demo,
            )
        if path == "/message":
            args = MessageRequest.model_validate(payload)
            email = self.gmail.get(args.message_id)
            if email.sent_by_user:
                raise ValueError("Select an incoming email")
            thread = self.gmail.thread(email)
            identity = self.gmail.identity()
            from src.Gmail.sender import reply_for

            preview = reply_for(email, identity, "preview")
            summary = self.assistant.summarize(email, thread)
            self.confirmed = {
                key: value
                for key, value in self.confirmed.items()
                if time.monotonic() - value[1] < 86400
            }
            self.confirmed[args.message_id] = (email.thread_id, time.monotonic())
            return {
                "message_id": email.id,
                "body": email.body,
                "sender": email.sender,
                "summary": summary.model_dump(),
                "to": preview.to,
                "cc": preview.cc,
                "subject": preview.subject,
            }
        if path == "/generate":
            args = GenerateRequest.model_validate(payload)
            if args.message_id not in self.confirmed:
                raise ValueError("Select and summarize the incoming message first")
            email = self.gmail.get(args.message_id)
            if email.sent_by_user:
                raise ValueError("Select an incoming email")
            return self.assistant.run(
                email, args.intent, self.gmail.thread(email)
            ).public()
        if path == "/confirm-sent":
            args = MessageRequest.model_validate(payload)
            # Only allow actual SENT messages from a recently selected thread.
            email = self.gmail.confirm_sent(args.message_id)
            now = time.monotonic()
            threads = {
                thread
                for thread, stamp in self.confirmed.values()
                if now - stamp < 86400
            }
            if not email.thread_id or email.thread_id not in threads:
                raise ValueError(
                    "Sent message must belong to a recently selected thread"
                )
            self.memory.remember_sent(email)
            return {"stored": True, "source_message_id": email.id}
        raise RejectedRequest(404, "Unknown endpoint")


def handler_for(backend):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ReplyBackend"
        sys_version = ""

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, format, *args):
            pass  # URLs, request data and exception payloads are private by default.

        def respond(self, status, data):
            self.respond_bytes(status, json.dumps(data).encode(), "application/json")

        def respond_bytes(self, status, body, content_type):
            self.send_response(status)
            if backend.allowed_origin(self.headers.get("Origin")):
                self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
                self.send_header("Vary", "Origin")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Type", content_type)
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            )
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def do_GET(self):
            try:
                if self.headers.get("Host") != f"127.0.0.1:{backend.config.port}":
                    raise RejectedRequest(403, "Invalid Host")
                if self.headers.get(
                    "Origin"
                ) is not None and not backend.allowed_origin(self.headers["Origin"]):
                    raise RejectedRequest(403, "Origin rejected")
                files = {
                    "/": ("index.html", "text/html; charset=utf-8"),
                    "/dashboard.js": ("dashboard.js", "application/javascript"),
                    "/dashboard.css": ("dashboard.css", "text/css"),
                }
                if self.path not in files:
                    raise RejectedRequest(404, "Unknown page")
                name, mime = files[self.path]
                # Static shell only: email data and tokens always require API authentication.
                body = (
                    Path(__file__).resolve().parent / "dashboard" / name
                ).read_bytes()
                self.respond_bytes(200, body, mime)
            except RejectedRequest as error:
                self.respond(error.status, {"error": error.message})

        def do_OPTIONS(self):
            try:
                backend.authorize(self.headers, preflight=True)
                if self.path not in (
                    "/message",
                    "/generate",
                    "/confirm-sent",
                    "/queue",
                ):
                    raise RejectedRequest(404, "Unknown endpoint")
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header(
                    "Access-Control-Allow-Headers", "Authorization, Content-Type"
                )
                self.send_header("Vary", "Origin")
                self.send_header("Content-Length", "0")
                self.end_headers()
            except RejectedRequest as error:
                self.respond(error.status, {"error": error.message})

        def do_POST(self):
            try:
                backend.authorize(self.headers)
                if self.headers.get("Content-Type") != "application/json":
                    raise RejectedRequest(415, "Expected application/json")
                if self.headers.get("Transfer-Encoding"):
                    raise RejectedRequest(400, "Chunked requests are unsupported")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 32768:
                    raise RejectedRequest(413, "Request body must be 1..32768 bytes")
                payload = json.loads(self.rfile.read(length))
                result = backend.dispatch(self.path, payload)
                self.respond(200, result)
            except RejectedRequest as error:
                self.respond(error.status, {"error": error.message})
            except (ValueError, TypeError):
                self.respond(400, {"error": "Invalid request or message state"})
            except Exception:
                self.respond(
                    503,
                    {
                        "error": "Backend service failed; check Gmail authentication and Ollama availability"
                    },
                )

    return Handler


def make_server(backend):
    # Single request at a time prevents concurrent access to OAuth/model state.
    return HTTPServer(("127.0.0.1", backend.config.port), handler_for(backend))


def serve(config=None, demo=False):
    from src.Gmail.client import authenticate, GmailClient
    from src.Model.Llama import Model
    from src.Model.memry.Vector_lib import Memory
    from src.pipeline import Assistant

    config = config or Config.from_env()
    token_file = Path(config.backend_token_path)
    token = (
        token_file.read_text().strip()
        if token_file.exists()
        else secrets.token_urlsafe(32)
    )
    private_write(token_file, token)
    if demo:
        from src.demo import DemoMailbox, DemoModel, DemoMemory

        memory = DemoMemory()
        gmail, model = DemoMailbox(), DemoModel()
        print(
            "SYNTHETIC DEMO: mailbox and model outputs are simulated; delivery and memory confirmation are unavailable."
        )
    else:
        memory = Memory(config)
        gmail, model = GmailClient(authenticate(config), config), Model(config)
    backend = Backend(
        gmail, Assistant(model, memory, config), memory, token, config, demo=demo
    )
    with make_server(backend) as server:
        print(
            f"Dashboard: http://127.0.0.1:{config.port}. Pair using the private token file; sending stays in Gmail."
        )
        server.serve_forever()
