"""Actual MV3 popup + mock-service backend QA in a fresh Chrome profile.

No real Gmail page, account, OAuth token, or model service is accessed.
Chrome's pipe-based extension debugging is restricted to this temporary process.
"""

import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import threading
import time
from unittest.mock import Mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend import Backend, make_server
from src.config import Config
from src.demo import DEMO_EMAIL, DemoModel, DemoMailbox
from src.pipeline import Assistant

ROOT = Path(__file__).resolve().parents[1]


def smoke():
    with tempfile.TemporaryDirectory(prefix="gmail-extension-qa-") as profile:
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen(
                [
                    "/bin/bash",
                    "-c",
                    'exec "$@" 3<&0 4>&1',
                    "chrome-smoke",
                    "google-chrome",
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--remote-debugging-pipe",
                    "--enable-unsafe-extension-debugging",
                    "--user-data-dir=" + profile,
                    "about:blank",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
            )
            serial, pending = 0, b""
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)

            def command(method, params=None, session=None):
                nonlocal serial, pending
                serial += 1
                message = {"id": serial, "method": method, "params": params or {}}
                if session:
                    message["sessionId"] = session
                process.stdin.write(json.dumps(message).encode() + b"\0")
                process.stdin.flush()
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if b"\0" not in pending:
                        if not selector.select(timeout=1):
                            continue
                        chunk = os.read(process.stdout.fileno(), 65536)
                        if not chunk:
                            raise RuntimeError("Chrome exited unexpectedly")
                        pending += chunk
                        continue
                    raw, pending = pending.split(b"\0", 1)
                    reply = json.loads(raw)
                    if reply.get("id") == serial:
                        if "error" in reply:
                            raise RuntimeError(reply["error"]["message"])
                        return reply.get("result", {})
                raise RuntimeError("Chrome command timed out")

            server, worker = None, None
            try:
                extension_id = command(
                    "Extensions.loadUnpacked", {"path": str(ROOT / "extension")}
                )["id"]
                origin = "chrome-extension://" + extension_id
                gmail, memory = DemoMailbox(), Mock()
                memory.retrieve.return_value = []
                gmail.items["review"] = gmail.items["review"].model_copy(
                    update={"subject": "<img src=x onerror=alert(1)>"}
                )
                token = "synthetic-browser-qa-token-at-least-32-chars"
                backend = Backend(
                    gmail,
                    Assistant(DemoModel(), memory),
                    memory,
                    token,
                    Config(extension_origin=origin),
                    demo=True,
                )
                server = make_server(backend)
                worker = threading.Thread(target=server.serve_forever, daemon=True)
                worker.start()
                target = command(
                    "Target.createTarget", {"url": origin + "/popup.html"}
                )["targetId"]
                session = command(
                    "Target.attachToTarget", {"targetId": target, "flatten": True}
                )["sessionId"]

                def evaluate(expression):
                    result = command(
                        "Runtime.evaluate",
                        {
                            "expression": expression,
                            "returnByValue": True,
                            "awaitPromise": True,
                        },
                        session,
                    )
                    if result.get("exceptionDetails"):
                        raise RuntimeError(
                            "Popup JavaScript failed: "
                            + result["exceptionDetails"]["text"]
                        )
                    return result["result"].get("value")

                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if evaluate("Boolean(document.getElementById('pair'))"):
                        break
                    time.sleep(0.1)
                assert (
                    evaluate("document.getElementById('origin').textContent") == origin
                )
                evaluate(
                    "document.getElementById('token').value="
                    + json.dumps(token)
                    + "; document.getElementById('pair').click()"
                )
                time.sleep(0.3)
                assert evaluate("document.getElementById('token').value") == ""
                assert evaluate(
                    "chrome.storage.session.get('pairingToken').then(x=>Boolean(x.pairingToken))"
                )
                assert evaluate("document.getElementById('generate').disabled")
                assert (
                    evaluate(
                        "api('/message',{message_id:'synthetic-incoming'}).then(x=>x.summary.requests.length)"
                    )
                    == 1
                )
                evaluate(
                    "selected='synthetic-incoming'; document.getElementById('intent').value='yeah sure'; document.getElementById('generate').disabled=false; document.getElementById('generate').click()"
                )
                deadline = time.monotonic() + 5
                while evaluate("busy") and time.monotonic() < deadline:
                    time.sleep(0.1)
                assert evaluate("document.getElementById('draft').value").startswith(
                    "Yes, I can attend"
                )
                assert evaluate(
                    "document.getElementById('status').textContent"
                ).startswith("Evaluator passed")
                memory.remember_sent.assert_not_called()
                evaluate("document.getElementById('reject').click()")
                time.sleep(0.1)
                assert evaluate("document.getElementById('draft').value") == ""
                print(
                    "PASS: actual MV3 popup loaded; session pairing, authenticated HTTP summary/generation, evaluation display and rejection verified with synthetic services."
                )
                # Test the local dashboard against the same synthetic services.
                target = command(
                    "Target.createTarget", {"url": "http://127.0.0.1:8765/"}
                )["targetId"]
                session = command(
                    "Target.attachToTarget", {"targetId": target, "flatten": True}
                )["sessionId"]
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if evaluate("Boolean(document.getElementById('connect'))"):
                        break
                    time.sleep(0.1)
                evaluate(
                    "document.getElementById('token').value="
                    + json.dumps(token)
                    + "; document.querySelector('#connect button').click()"
                )
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if evaluate("document.getElementById('pairing').hidden"):
                        break
                    time.sleep(0.1)
                assert (
                    evaluate("document.querySelectorAll('#list .message').length") == 1
                )
                assert (
                    evaluate("document.getElementById('count-filtered').textContent")
                    == "3"
                )
                evaluate("document.querySelector('[data-category=review]').click()")
                assert (
                    evaluate(
                        "document.querySelector('#list .message-subject').textContent"
                    )
                    == "<img src=x onerror=alert(1)>"
                )
                assert evaluate("document.querySelectorAll('#list img').length") == 0
                evaluate("document.querySelector('[data-category=filtered]').click()")
                assert (
                    evaluate("document.querySelectorAll('#list .message').length") == 3
                )
                evaluate(
                    "document.querySelector('[data-category=needs_reply]').click(); document.querySelector('#list .message').click()"
                )
                deadline = time.monotonic() + 5
                while evaluate("detailBusy") and time.monotonic() < deadline:
                    time.sleep(0.1)
                assert evaluate("document.getElementById('generate').disabled") is False
                evaluate(
                    "document.getElementById('intent').value='yeah sure'; document.getElementById('generate').click()"
                )
                deadline = time.monotonic() + 5
                while evaluate("detailBusy") and time.monotonic() < deadline:
                    time.sleep(0.1)
                assert evaluate("document.getElementById('draft').value").startswith(
                    "Yes, I can attend"
                )
                assert evaluate(
                    "document.getElementById('evaluation').textContent"
                ).startswith("Evaluator passed")
                command(
                    "Emulation.setDeviceMetricsOverride",
                    {
                        "width": 1440,
                        "height": 1000,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    },
                    session,
                )
                import base64

                screenshot = command(
                    "Page.captureScreenshot",
                    {"format": "png", "captureBeyondViewport": False},
                    session,
                )
                Path("/tmp/gmail-reply-dashboard.png").write_bytes(
                    base64.b64decode(screenshot["data"])
                )
                evaluate("document.getElementById('reject').click()")
                assert evaluate("document.getElementById('draft').value") == ""
                evaluate("document.getElementById('disconnect').click()")
                assert evaluate("sessionStorage.getItem('reply-desk-token')") is None
                assert evaluate("document.getElementById('original').textContent") == ""
                memory.remember_sent.assert_not_called()
                print(
                    "PASS: actual local dashboard pairing, automatic queue load, spam/automation filters, selection, summary, drafting, rejection and disconnect verified with synthetic services."
                )

            finally:
                if server:
                    server.shutdown()
                    server.server_close()
                    worker.join()
                selector.close()
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process.stdin.close()
                process.stdout.close()


if __name__ == "__main__":
    smoke()
