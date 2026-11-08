"""Structured JSON logging with request correlation and secret redaction.

Pattern credit: request-correlated structured logging is adapted from
fastapi-langgraph-agent-production-ready-template (structlog + asgi-correlation-id). IAT uses the
standard library only, to avoid two extra dependencies for the same outcome.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

SENSITIVE_KEYS = frozenset(
    {"authorization", "token", "access_token", "jwt", "secret", "password", "api_key", "cookie"}
)
REDACTED = "[REDACTED]"
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_.=]+")
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+")

_STANDARD_ATTRS = frozenset(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


def redact_text(text: str) -> str:
    text = _BEARER_RE.sub(f"Bearer {REDACTED}", text)
    return _JWT_RE.sub(REDACTED, text)


def redact_value(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {k: redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [redact_value(key, v) for v in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": redact_text(record.getMessage()),
        }
        request_id = request_id_var.get()
        if request_id:
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = redact_value(key, value)
        if record.exc_info and record.exc_info[0] is not None:
            payload["error_class"] = record.exc_info[0].__name__
        return json.dumps(payload, default=str)


class _StdoutHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Writes to whatever ``sys.stdout`` is at emit time (works with redirection and capture)."""

    @property
    def stream(self) -> Any:
        return sys.stdout

    @stream.setter
    def stream(self, _: Any) -> None:
        pass


def configure_logging(level: str = "INFO") -> None:
    handler = _StdoutHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("iat")
    root.handlers = [handler]
    root.setLevel(level.upper())
    root.propagate = False
