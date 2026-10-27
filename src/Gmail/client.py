"""Gmail access is explicit and injectable for QA; read errors propagate."""

from pathlib import Path
from src.config import Config, private_write
from src.Gmail.reader import parse_message, parse_metadata

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class AuthenticationRequired(RuntimeError):
    pass


def authenticate(config: Config, interactive=False, allow_send=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    scopes = SCOPES + (
        ["https://www.googleapis.com/auth/gmail.send"] if allow_send else []
    )
    creds = None
    try:
        if Path(config.token_path).exists():
            creds = Credentials.from_authorized_user_file(config.token_path)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid or not creds.has_scopes(scopes):
            if not interactive:
                raise AuthenticationRequired(
                    "Run the explicit auth command to authorize Gmail"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                config.credentials_path, scopes
            )
            creds = flow.run_local_server(port=0)
    except AuthenticationRequired:
        raise
    except Exception:
        raise AuthenticationRequired(
            "Gmail authentication failed; reauthorize with auth"
        ) from None
    private_write(config.token_path, creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


class GmailClient:
    def __init__(self, service, config=None):
        self.service = service
        self.config = config or Config()

    def messages(self, label="INBOX", limit=10, query=""):
        if not 0 <= limit <= 1000:
            raise ValueError("Message limit must be 0..1000")
        result, page = [], None
        while len(result) < limit:
            args = dict(
                userId="me",
                labelIds=[label],
                maxResults=min(100, limit - len(result)),
                q=query,
                includeSpamTrash=False,
            )
            if page:
                args["pageToken"] = page
            response = self.service.users().messages().list(**args).execute()
            result.extend(item["id"] for item in response.get("messages", []))
            page = response.get("nextPageToken")
            if not page:
                break
        return result[:limit]

    def inbox_page(self, limit=100, query="", page_token=""):
        if not 1 <= limit <= 500:
            raise ValueError("Inbox page limit must be 1..500")
        args = dict(
            userId="me",
            labelIds=["INBOX"],
            maxResults=limit,
            q=query,
            includeSpamTrash=False,
        )
        if page_token:
            args["pageToken"] = page_token
        return self.service.users().messages().list(**args).execute()

    def metadata(self, message_id):
        result = (
            self.service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=[
                    "From",
                    "To",
                    "Cc",
                    "Reply-To",
                    "Subject",
                    "Message-ID",
                    "Auto-Submitted",
                    "Precedence",
                    "List-Unsubscribe",
                    "List-Id",
                ],
            )
            .execute()
        )
        return parse_metadata(result)

    def latest_in_thread(self, email):
        if not email.thread_id:
            return email
        result = (
            self.service.users()
            .threads()
            .get(
                userId="me",
                id=email.thread_id,
                format="metadata",
                metadataHeaders=[
                    "From",
                    "To",
                    "Cc",
                    "Reply-To",
                    "Subject",
                    "Message-ID",
                    "Auto-Submitted",
                    "Precedence",
                    "List-Unsubscribe",
                    "List-Id",
                ],
            )
            .execute()
        )
        candidates = [
            item
            for item in result.get("messages", [])
            if not {"DRAFT", "SPAM", "TRASH"} & set(item.get("labelIds", []))
        ]
        if not candidates:
            return email
        latest = max(candidates, key=lambda item: int(item.get("internalDate", "0")))
        return parse_metadata(latest)

    def get(self, message_id):
        result = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="raw")
            .execute()
        )
        return parse_message(result, self.config.context_chars)

    def thread(self, email):
        if not email.thread_id:
            return []
        raw = (
            self.service.users()
            .threads()
            .get(
                userId="me",
                id=email.thread_id,
                format="metadata",
                metadataHeaders=["Message-ID"],
            )
            .execute()
        )
        messages = raw.get("messages", [])
        # Only context before the selected message, never later replies.
        ids = [item["id"] for item in messages]
        if email.id not in ids:
            raise ValueError("Selected message absent from thread")
        previous = ids[: ids.index(email.id)][-self.config.thread_limit :]
        result, budget = [], self.config.context_chars - len(email.body)
        for message_id in reversed(previous):
            if budget <= 0:
                break
            item = self.get(message_id)
            item = item.model_copy(update={"body": item.body[:budget]})
            budget -= len(item.body)
            result.insert(0, item)
        return result

    def identity(self):
        return (
            self.service.users()
            .getProfile(userId="me")
            .execute()["emailAddress"]
            .lower()
        )

    def confirm_sent(self, message_id):
        email = self.get(message_id)
        if not email.sent_by_user:
            raise ValueError("Message is not confirmed SENT by Gmail")
        return email
