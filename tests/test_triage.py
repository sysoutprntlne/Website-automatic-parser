import unittest
from unittest.mock import Mock
from src.config import Config
from src.demo import DEMO_EMAIL
from src.triage import ReplyQueue, classify
from src.Gmail.reader import parse_metadata


class TriageTests(unittest.TestCase):
    def test_filter_reasons_and_uncertain_human_mail(self):
        for update in (
            {"labels": ["SPAM"]},
            {"labels": ["CATEGORY_PROMOTIONS"]},
            {"auto_submitted": "auto-generated"},
            {"list_mail": True},
            {"precedence": "bulk"},
            {"sender": "no-reply@example.test"},
            {"sent_by_user": True},
        ):
            category, reason = classify(DEMO_EMAIL.model_copy(update=update))
            self.assertEqual(category, "filtered")
            self.assertTrue(reason)
        self.assertEqual(classify(DEMO_EMAIL)[0], "needs_reply")
        self.assertEqual(
            classify(DEMO_EMAIL.model_copy(update={"body": "Here are the notes."}))[0],
            "review",
        )
        self.assertEqual(
            classify(DEMO_EMAIL.model_copy(update={"auto_submitted": "no"}))[0],
            "needs_reply",
        )

    def test_metadata_headers_without_model_or_raw_body(self):
        email = parse_metadata(
            {
                "id": "m",
                "labelIds": ["INBOX", "UNREAD"],
                "snippet": "Please confirm &amp; reply",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "Bot <noreply@example.test>"},
                        {"name": "Auto-Submitted", "value": "auto-generated"},
                        {
                            "name": "List-Unsubscribe",
                            "value": "<https://example.test/unsubscribe>",
                        },
                    ]
                },
            }
        )
        self.assertTrue(email.list_mail)
        self.assertEqual(email.body, "Please confirm & reply")
        self.assertEqual(classify(email)[0], "filtered")

    def test_dedupe_replied_threads_cache_and_partial_errors(self):
        gmail = Mock()
        gmail.inbox_page.return_value = {
            "messages": [{"id": i} for i in ["one", "two", "bad"]]
        }
        gmail.metadata.side_effect = [
            DEMO_EMAIL,
            DEMO_EMAIL,
            RuntimeError("synthetic error"),
        ]
        gmail.latest_in_thread.return_value = DEMO_EMAIL.model_copy(
            update={"sent_by_user": True}
        )
        queue = ReplyQueue(gmail)
        result = queue.scan()
        self.assertEqual(result["counts"]["filtered"], 1)
        self.assertEqual(result["failed_messages"], 1)
        gmail.latest_in_thread.assert_called_once()
        self.assertIs(queue.scan(), result)
        gmail.inbox_page.assert_called_once_with(limit=100, query="", page_token="")
        gmail.metadata.side_effect = None
        gmail.metadata.return_value = DEMO_EMAIL
        self.assertEqual(queue.scan(refresh=True)["failed_messages"], 0)

    def test_empty_and_scan_limit_reported(self):
        gmail = Mock()
        gmail.inbox_page.return_value = {}
        self.assertEqual(ReplyQueue(gmail).scan()["items"], [])
        gmail.inbox_page.return_value = {
            "messages": [{"id": "one"}],
            "nextPageToken": "older",
        }
        gmail.metadata.return_value = gmail.latest_in_thread.return_value = DEMO_EMAIL
        queue = ReplyQueue(gmail, Config(dashboard_limit=1))
        self.assertEqual(queue.scan()["next_page_token"], "older")
        queue.scan(page_token="older")
        gmail.inbox_page.assert_called_with(limit=1, query="", page_token="older")

    def test_gmail_pagination_and_latest_sent_ignores_drafts(self):
        from unittest.mock import MagicMock
        from src.Gmail.client import GmailClient

        service = MagicMock()
        client = GmailClient(service)
        service.users().messages().list().execute.return_value = {
            "messages": [],
            "nextPageToken": "next",
        }
        self.assertEqual(client.inbox_page(page_token="older")["nextPageToken"], "next")
        args = service.users().messages().list.call_args.kwargs
        self.assertFalse(args["includeSpamTrash"])
        self.assertEqual(args["pageToken"], "older")
        self.assertEqual(args["labelIds"], ["INBOX"])
        service.users().threads().get().execute.return_value = {
            "messages": [
                {
                    "id": "incoming",
                    "internalDate": "100",
                    "labelIds": ["INBOX"],
                    "payload": {},
                },
                {
                    "id": "sent",
                    "internalDate": "200",
                    "labelIds": ["SENT"],
                    "payload": {},
                },
                {
                    "id": "draft",
                    "internalDate": "300",
                    "labelIds": ["DRAFT"],
                    "payload": {},
                },
            ]
        }
        latest = client.latest_in_thread(DEMO_EMAIL)
        self.assertEqual(latest.id, "sent")
        self.assertTrue(latest.sent_by_user)
