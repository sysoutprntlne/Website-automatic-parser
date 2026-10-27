import base64
import unittest
from email.message import EmailMessage
from unittest.mock import MagicMock
from src.config import Config
from src.Gmail.reader import parse_message
from src.Gmail.client import GmailClient
from src.Gmail.sender import (
    reply_for,
    send_gmail_msg,
    approval_digest,
    DeliveryUncertain,
)


def fixture(body="Can you attend Tuesday at 3?", html=False, sent=False, id="m1"):
    msg = EmailMessage()
    msg["From"] = "Requester <requester@example.test>"
    msg["To"] = "Me <me@example.test>, Other <other@example.test>"
    msg["Reply-To"] = "desk@example.test"
    msg["Cc"] = "cc@example.test"
    msg["Subject"] = "Meeting"
    msg["Message-ID"] = "<m1@example.test>"
    msg["References"] = "<old@example.test>"
    msg.set_content(body, subtype="html" if html else "plain")
    return dict(
        id=id,
        threadId="t1",
        internalDate="1000",
        labelIds=["SENT"] if sent else ["INBOX"],
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode(),
    )


class GmailTests(unittest.TestCase):
    def test_plain_html_and_multipart(self):
        self.assertEqual(parse_message(fixture()).sender, "requester@example.test")
        self.assertEqual(
            parse_message(
                fixture("<p>Hello &amp; welcome</p><script>bad</script>", True)
            ).body,
            "Hello & welcome",
        )
        msg = EmailMessage()
        msg.set_content("Plain preferred")
        msg.add_alternative("<p>HTML</p>", subtype="html")
        raw = fixture()
        raw["raw"] = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self.assertEqual(parse_message(raw).body.strip(), "Plain preferred")

    def test_addressing_and_threading(self):
        reply = reply_for(parse_message(fixture()), "me@example.test", "Yes", True)
        self.assertEqual(reply.to, ["desk@example.test"])
        self.assertEqual(reply.cc, ["other@example.test", "cc@example.test"])
        self.assertEqual(reply.in_reply_to, "<m1@example.test>")
        self.assertEqual(reply.subject, "Re: Meeting")

    def test_send_once_and_exact_approval(self):
        service = MagicMock()
        client = GmailClient(service)
        service.users().getProfile().execute.return_value = {
            "emailAddress": "me@example.test"
        }
        reply = reply_for(parse_message(fixture()), "me@example.test", "Yes")
        with self.assertRaises(ValueError):
            send_gmail_msg(client, reply, "not-approved")
        service.users().messages().send().execute.side_effect = TimeoutError()
        with self.assertRaises(DeliveryUncertain):
            send_gmail_msg(client, reply, approval_digest(reply))
        service.users().messages().send().execute.assert_called_once_with(num_retries=0)
        sent = next(
            call.kwargs["body"]
            for call in service.users().messages().send.call_args_list
            if "body" in call.kwargs
        )
        self.assertEqual(sent["threadId"], "t1")
        self.assertIn(
            b"In-Reply-To: <m1@example.test>", base64.urlsafe_b64decode(sent["raw"])
        )

    def test_empty_inbox_and_api_failure(self):
        service = MagicMock()
        client = GmailClient(service)
        service.users().messages().list().execute.return_value = {}
        self.assertEqual(client.messages(), [])
        service.users().messages().list().execute.side_effect = RuntimeError("API")
        with self.assertRaises(RuntimeError):
            client.messages()

    def test_bounded_thread_and_no_future(self):
        service = MagicMock()
        client = GmailClient(service, Config(context_chars=50, thread_limit=2))
        service.users().threads().get().execute.return_value = {
            "messages": [{"id": i} for i in ["a", "b", "m1", "future"]]
        }
        service.users().messages().get().execute.side_effect = [
            fixture("b" * 20, id="b"),
            fixture("a" * 20, id="a"),
        ]
        selected = parse_message(fixture("selected"))
        context = client.thread(selected)
        self.assertEqual([e.id for e in context], ["a", "b"])
        self.assertLessEqual(sum(len(e.body) for e in context) + len(selected.body), 50)

    def test_unsent_cannot_be_confirmed(self):
        service = MagicMock()
        service.users().messages().get().execute.return_value = fixture()
        with self.assertRaises(ValueError):
            GmailClient(service).confirm_sent("m1")
