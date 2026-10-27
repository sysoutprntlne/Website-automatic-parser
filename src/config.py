"""Configuration is loaded explicitly; importing never opens services."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    model: str = "llama3.2:1b-instruct-q4_K_M"
    evaluator_model: str = "llama3.2:1b-instruct-q4_K_M"
    ollama_host: str = "http://127.0.0.1:11434"
    memory_path: str = "private/memory"
    retrieval_limit: int = 4
    style_chars: int = 6000
    context_chars: int = 16000
    thread_limit: int = 8
    attempts: int = 3
    temperature: float = 0.2
    seed: int = 42
    credentials_path: str = "lib/cred/credentials.json"
    token_path: str = "lib/cred/token.json"
    backend_token_path: str = "private/backend-token"
    extension_origin: str = ""
    port: int = 8765
    dashboard_limit: int = 100
    dashboard_refresh_seconds: int = 60
    dashboard_query: str = ""

    def __post_init__(self):
        for name in (
            "style_chars",
            "context_chars",
            "thread_limit",
            "attempts",
            "port",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if not 0 <= self.retrieval_limit <= 30 or self.attempts > 10:
            raise ValueError("retrieval_limit must be 0..30 and attempts 1..10")
        if not 1 <= self.dashboard_limit <= 500 or self.dashboard_refresh_seconds < 30:
            raise ValueError(
                "Dashboard limit must be 1..500 and refresh at least 30 seconds"
            )
        if not 1 <= self.port <= 65535:
            raise ValueError("Invalid port")

    @classmethod
    def from_env(cls):
        values = {}
        defaults = cls()
        for name in cls.__dataclass_fields__:
            value = os.environ.get("REPLY_" + name.upper())
            if value is not None:
                default = getattr(defaults, name)
                values[name] = type(default)(value)
        return cls(**values)


def private_write(path, text):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(text)
