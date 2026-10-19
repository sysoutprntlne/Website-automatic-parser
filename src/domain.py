"""Small validated objects shared by Gmail, models and the interface."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Email(Record):
    id: str
    thread_id: str = ""
    sender: str
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    reply_to: list[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    timestamp: str = ""
    message_id: str = ""
    references: str = ""
    sent_by_user: bool = False
    labels: list[str] = Field(default_factory=list)
    auto_submitted: str = ""
    precedence: str = ""
    list_mail: bool = False


class Summary(Record):
    overview: str = Field(min_length=1, max_length=4000)
    requests: list[str]
    deadlines: list[str]


class Draft(Record):
    body: str = Field(max_length=12000)
    missing_information: list[str]

    @field_validator("body")
    @classmethod
    def body_or_question(cls, value):
        return value.strip()


class Evaluation(Record):
    passed: bool
    issues: list[str]


class Reply(Record):
    to: list[str]
    cc: list[str] = Field(default_factory=list)
    subject: str
    body: str = Field(min_length=1, max_length=12000)
    thread_id: str
    in_reply_to: str
    references: str

    @field_validator("to", "cc")
    @classmethod
    def addresses(cls, values):
        import re
        if any(not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+", value) for value in values):
            raise ValueError("Use bare valid email addresses")
        return values

    @field_validator("subject", "in_reply_to", "references", "thread_id")
    @classmethod
    def no_header_injection(cls, value):
        if "\r" in value or "\n" in value:
            raise ValueError("Newlines forbidden in headers")
        return value
