import http.client
import json
import threading
import unittest
from unittest.mock import Mock
from src.backend import Backend, RejectedRequest, make_server
from src.config import Config
from src.demo import DEMO_EMAIL, DemoModel
from src.pipeline import Assistant

ORIGIN = "chrome-extension://" + "a" * 32
TOKEN = "test-token-" * 5


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.gmail, self.memory = Mock(), Mock()
        self.gmail.get.return_value = DEMO_EMAIL
        self.gmail.identity.return_value = "me@example.test"
        self.gmail.thread.return_value = []
        self.memory.retrieve.return_value = []
        self.backend = Backend(
            self.gmail,
            Assistant(DemoModel(), self.memory),
            self.memory,
            TOKEN,
            Config(extension_origin=ORIGIN),
        )

    def test_origin_auth_host_checks(self):
        good = {
            "Host": "127.0.0.1:8765",
            "Origin": ORIGIN,
            "Authorization": "Bearer " + TOKEN,
        }
        self.backend.authorize(good)
        for changed in (
            {"Origin": "https://evil.example"},
            {"Authorization": "bad"},
            {"Host": "evil.example:8765"},
        ):
            with self.assertRaises(RejectedRequest):
                self.backend.authorize(dict(good, **changed))
        self.backend.authorize(good, preflight=True)

    def test_end_to_end_mock_workflow_only_sent_stored(self):
        self.backend.dispatch("/message", {"message_id": DEMO_EMAIL.id})
        result = self.backend.dispatch(
            "/generate", {"message_id": DEMO_EMAIL.id, "intent": "yeah sure"}
        )
        self.assertTrue(result["evaluation_passed"])
        self.memory.remember_sent.assert_not_called()
        final = DEMO_EMAIL.model_copy(
            update={
                "id": "sent-1",
                "sent_by_user": True,
                "body": "User edited final text.",
            }
        )
        self.gmail.confirm_sent.return_value = final
        self.backend.dispatch("/confirm-sent", {"message_id": "sent-1"})
        self.memory.remember_sent.assert_called_once_with(final)

    def test_validation_and_no_send_endpoint(self):
        with self.assertRaises(ValueError):
            self.backend.dispatch("/message", {"message_id": "id", "body": "forbidden"})
        with self.assertRaises(ValueError):
            self.backend.dispatch("/generate", {"message_id": "id", "intent": "yes"})
        with self.assertRaises(RejectedRequest):
            self.backend.dispatch("/send", {})
        self.gmail.confirm_sent.return_value = DEMO_EMAIL.model_copy(
            update={"sent_by_user": True}
        )
        with self.assertRaises(ValueError):
            self.backend.dispatch("/confirm-sent", {"message_id": "sent"})
        self.memory.remember_sent.assert_not_called()

    def test_http_validation(self):
        # Port zero is assigned by OS for QA, then Host validation uses that exact port.
        from src.backend import handler_for
        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", 0), handler_for(self.backend))
        from dataclasses import replace

        self.backend.config = replace(self.backend.config, port=server.server_port)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:

            def request(path, body, headers, method="POST"):
                connection = http.client.HTTPConnection(
                    "127.0.0.1", server.server_port, timeout=3
                )
                connection.request(method, path, body, headers)
                response = connection.getresponse()
                result = (
                    response.status,
                    response.read(),
                    response.getheader("Access-Control-Allow-Origin"),
                )
                connection.close()
                return result

            good = {
                "Origin": ORIGIN,
                "Authorization": "Bearer " + TOKEN,
                "Content-Type": "application/json",
            }
            status, body, origin = request(
                "/message", json.dumps({"message_id": DEMO_EMAIL.id}), good
            )
            self.assertEqual(status, 200)
            self.assertEqual(origin, ORIGIN)
            self.assertEqual(
                request("/message", "{}", dict(good, Origin="https://evil.test"))[0],
                403,
            )
            self.assertEqual(
                request("/message", "{}", dict(good, Authorization="bad"))[0], 401
            )
            self.assertEqual(
                request("/message", "{}", dict(good, **{"Content-Type": "text/plain"}))[
                    0
                ],
                415,
            )
            self.assertEqual(request("/message", "invalid", good)[0], 400)
            self.assertEqual(request("/message", "x" * 32769, good)[0], 413)
            self.assertEqual(request("/send", "{}", good)[0], 404)
            self.assertEqual(
                request("/generate", "", {"Origin": ORIGIN}, "OPTIONS")[0], 204
            )
        finally:
            server.shutdown()
            server.server_close()
            worker.join()
