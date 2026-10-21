"""Deterministic Gmail MIME parsing. No authentication or model calls here."""

import base64
import re
from email import policy
from email.parser import BytesParser, HeaderParser
from email.utils import getaddresses
from html.parser import HTMLParser
from html import unescape

from src.domain import Email


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("br", "p", "div", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def addresses(value):
    return list(
        dict.fromkeys(
            a.lower()
            for _, a in getaddresses([value])
            if re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+", a)
        )
    )

# Creates usable format for model
def parse_message(raw, max_chars=16000):
    """Decode Gmail format=raw using Python's charset-aware MIME parser."""
    encoded = raw["raw"]
    data = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    msg = BytesParser(policy=policy.default).parsebytes(data)
    part = msg.get_body(preferencelist=("plain", "html"))
    body = ""
    if part:
        body = part.get_content()
        if part.get_content_type() == "text/html":
            parser = TextHTML()
            parser.feed(body)
            body = "".join(parser.parts).strip()
    return from_headers(raw, msg, body[:max_chars])


def parse_metadata(raw, max_chars=300):
    headers = raw.get("payload", {}).get("headers", [])
    msg = HeaderParser(policy=policy.default).parsestr(
        "\r\n".join(item["name"] + ": " + item["value"] for item in headers)
        + "\r\n\r\n"
    )
    return from_headers(raw, msg, unescape(raw.get("snippet", ""))[:max_chars])


def from_headers(raw, msg, body):
    headers = lambda name: str(msg.get(name, ""))
    return Email(
        id=raw["id"],
        thread_id=raw.get("threadId", ""),
        sender=next(iter(addresses(headers("From"))), ""),
        to=addresses(headers("To")),
        cc=addresses(headers("Cc")),
        reply_to=addresses(headers("Reply-To")),
        subject=headers("Subject"),
        body=body,
        timestamp=str(raw.get("internalDate", "")),
        message_id=headers("Message-ID"),
        references=headers("References"),
        sent_by_user="SENT" in raw.get("labelIds", []),
        labels=raw.get("labelIds", []),
        auto_submitted=headers("Auto-Submitted").lower().strip(),
        precedence=headers("Precedence").lower().strip(),
        list_mail=bool(headers("List-Unsubscribe") or headers("List-Id")),
    )
