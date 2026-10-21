"""Deterministic synthetic services: demonstration only, not a real LLM."""

from src.domain import Email

DEMO_EMAIL = Email(
    id="synthetic-incoming",
    thread_id="demo-thread",
    sender="organizer@example.test",
    to=["me@example.test"],
    subject="Tuesday meeting",
    body="Are you able to attend Tuesday at 3?",
    message_id="<demo@example.test>",
)


class DemoModel:
    def __init__(self):
        self.calls = 0

    def metrics(self):
        return {"model_calls": self.calls, "prompt_tokens": None, "output_tokens": None}

    def structured(self, task, instructions, data, schema, evaluator=False):
        self.calls += 1
        if task == "summarize":
            result = dict(
                overview="The sender asks about attending a meeting.",
                requests=["Confirm whether you can attend Tuesday at 3."],
                deadlines=[],
            )
            demo_summaries = {
                "review": "The sender is sharing notes from your conversation. No explicit reply request.",
                "newsletter": "This is a weekly subscription reading list.",
                "no-reply": "This is an automated receipt for your records.",
                "promotion": "This is a promotional offer.",
            }
            incoming_id = data["incoming"]["id"]
            if incoming_id in demo_summaries:
                result = dict(
                    overview=demo_summaries[incoming_id], requests=[], deadlines=[]
                )
        elif task == "evaluate":
            result = dict(passed=True, issues=[])
        elif task == "draft":
            result = dict(
                body="Yes, I can attend Tuesday at 3. Thanks for checking!",
                missing_information=[],
            )
        else:
            raise ValueError("Unknown demo task")
        return schema.model_validate(result)


class DemoMailbox:
    """Read-only synthetic inbox for dashboard QA and local demonstrations."""

    def __init__(self):
        self.items = {
            "synthetic-incoming": DEMO_EMAIL.model_copy(
                update={"timestamp": "1792350000000", "labels": ["INBOX", "UNREAD"]}
            ),
            "review": DEMO_EMAIL.model_copy(
                update={
                    "id": "review",
                    "thread_id": "notes-thread",
                    "sender": "alex@example.test",
                    "subject": "Notes from our conversation",
                    "body": "Sharing the notes from our conversation. Thanks again.",
                    "timestamp": "1792340000000",
                }
            ),
            "newsletter": DEMO_EMAIL.model_copy(
                update={
                    "id": "newsletter",
                    "thread_id": "newsletter-thread",
                    "sender": "updates@example.test",
                    "subject": "Your weekly reading list",
                    "body": "The latest stories, delivered weekly.",
                    "list_mail": True,
                    "timestamp": "1792330000000",
                }
            ),
            "no-reply": DEMO_EMAIL.model_copy(
                update={
                    "id": "no-reply",
                    "thread_id": "receipt-thread",
                    "sender": "no-reply@example.test",
                    "subject": "Your receipt is ready",
                    "body": "An automated receipt for your records.",
                    "auto_submitted": "auto-generated",
                    "timestamp": "1792320000000",
                }
            ),
            "promotion": DEMO_EMAIL.model_copy(
                update={
                    "id": "promotion",
                    "thread_id": "promo-thread",
                    "sender": "offers@example.test",
                    "subject": "A special offer for you",
                    "body": "Our latest promotion.",
                    "labels": ["CATEGORY_PROMOTIONS"],
                    "timestamp": "1792310000000",
                }
            ),
        }

    def inbox_page(self, limit=100, query="", page_token=""):
        return {"messages": [{"id": key} for key in self.items][:limit]}

    def metadata(self, message_id):
        return self.items[message_id]

    def latest_in_thread(self, email):
        return email

    def get(self, message_id):
        return self.items[message_id]

    def thread(self, email):
        return []

    def identity(self):
        return "me@example.test"

    def confirm_sent(self, message_id):
        raise ValueError("Synthetic dashboard cannot confirm a real send")


class DemoMemory:
    def retrieve(self, *args, **kwargs):
        return []

    def remember_sent(self, email):
        raise ValueError("Synthetic dashboard does not persist email examples")
