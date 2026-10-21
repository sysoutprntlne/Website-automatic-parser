"""Read-only inbox triage. Heuristic suggestions, with inspectable filter reasons."""

import re
import time
from src.config import Config


def classify(email):
    labels = set(email.labels)
    if labels & {"SPAM", "TRASH", "DRAFT"}:
        return "filtered", "Gmail marked this as spam, trash, or a draft."
    if email.sent_by_user:
        return "filtered", "You sent the latest message in this conversation."
    if email.auto_submitted and email.auto_submitted != "no":
        return "filtered", "Sender marked this as an automated message."
    if email.precedence in ("bulk", "list", "junk") or email.list_mail:
        return "filtered", "Mailing list or bulk subscription message."
    local = email.sender.split("@")[0].lower()
    if re.search(r"(^|[._-])(no[._-]?reply|do[._-]?not[._-]?reply)([._-]|$)", local):
        return "filtered", "Sent from a no-reply address."
    if "CATEGORY_PROMOTIONS" in labels:
        return "filtered", "Gmail categorized this as a promotion."
    if not email.sender:
        return "review", "Sender could not be determined; review manually."
    if "?" in email.body or re.search(
        r"\b(please|could you|can you|let me know|confirm|deadline|rsvp)\b",
        email.subject + " " + email.body,
        re.I,
    ):
        return "needs_reply", "A question or request appears in the subject or preview."
    return "review", "May need your attention; no clear request in the preview."


class ReplyQueue:
    def __init__(self, gmail, config=None):
        self.gmail = gmail
        self.config = config or Config()
        self.cached = None
        self.cached_at = 0
        self.cached_page_token = None

    def scan(self, refresh=False, page_token=""):
        now = time.monotonic()
        if (
            self.cached is not None
            and page_token == self.cached_page_token
            and not refresh
            and now - self.cached_at < self.config.dashboard_refresh_seconds
        ):
            return self.cached
        page = self.gmail.inbox_page(
            limit=self.config.dashboard_limit,
            query=self.config.dashboard_query,
            page_token=page_token,
        )
        ids = [item["id"] for item in page.get("messages", [])]
        rows, seen, failed = [], set(), 0
        for message_id in ids:
            try:
                email = self.gmail.metadata(message_id)
                key = email.thread_id or email.id
                if key in seen:
                    continue
                # Check latest message even if the inbox still contains an older incoming email.
                latest = self.gmail.latest_in_thread(email)
                category, reason = classify(latest)
                seen.add(key)
                rows.append(
                    dict(
                        message_id=latest.id,
                        thread_id=latest.thread_id,
                        sender=latest.sender,
                        subject=latest.subject,
                        preview=latest.body[:300],
                        timestamp=latest.timestamp,
                        unread="UNREAD" in latest.labels,
                        sent_by_user=latest.sent_by_user,
                        category=category,
                        reason=reason,
                    )
                )
            except Exception:
                # One unavailable/deleted message must not hide the rest of the queue.
                failed += 1
        rows.sort(
            key=lambda item: (
                int(item["timestamp"]) if item["timestamp"].isdigit() else 0
            ),
            reverse=True,
        )
        self.cached = dict(
            items=rows,
            scanned=len(ids),
            scan_limit=self.config.dashboard_limit,
            next_page_token=page.get("nextPageToken", ""),
            failed_messages=failed,
            refreshed_at=int(time.time()),
            refresh_seconds=self.config.dashboard_refresh_seconds,
            counts={
                category: sum(row["category"] == category for row in rows)
                for category in ("needs_reply", "review", "filtered")
            },
        )
        self.cached_page_token = page_token
        self.cached_at = time.monotonic()
        return self.cached
