from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from app.core.log_context import actor_id_var, correlation_id_var, organization_id_var


_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


class ContextEnricherFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if not hasattr(record, "correlation_id"):
            record.correlation_id = correlation_id_var.get("-")
        if not hasattr(record, "organization_id"):
            record.organization_id = organization_id_var.get("-")
        if not hasattr(record, "actor_id"):
            record.actor_id = actor_id_var.get("-")
        return True


class SensitiveRedactionFilter(logging.Filter):
    _sensitive_keys = {
        "password",
        "token",
        "authorization",
        "secret",
        "email",
        "phone",
    }

    _redacted = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        # Redact sensitive extras
        for key in list(record.__dict__.keys()):
            if key.lower() in self._sensitive_keys:
                record.__dict__[key] = self._redacted

        # Redact message (best effort)
        try:
            message = record.getMessage()
        except Exception:
            return True

        record.redacted_message = self._redact_message(message)
        return True

    def _redact_message(self, message: str) -> str:
        redacted = message
        for key in self._sensitive_keys:
            # Matches: key=VALUE or key: VALUE (with optional quotes)
            pattern = re.compile(
                rf"(?i)(\b{re.escape(key)}\b\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;]+)"
            )
            redacted = pattern.sub(rf"\1{self._redacted}", redacted)
        return redacted


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = getattr(record, "redacted_message", None) or record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": message,
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", "-"),
            "organization_id": getattr(record, "organization_id", "-"),
            "actor_id": getattr(record, "actor_id", "-"),
        }

        # Include any explicit extras (action/entity_id/etc).
        for key, value in record.__dict__.items():
            if key in _RESERVED:
                continue
            if key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    env = os.getenv("ENV", "dev").lower()
    requested = os.getenv("LOG_LEVEL", "INFO").upper()

    requested_levelno = logging.getLevelName(requested)
    if isinstance(requested_levelno, str):
        requested_levelno = logging.INFO

    # Production clamp: never allow DEBUG (or anything below INFO).
    effective_levelno = requested_levelno
    if env == "prod" and effective_levelno < logging.INFO:
        effective_levelno = logging.INFO

    root = logging.getLogger()
    root.setLevel(effective_levelno)

    handler = logging.StreamHandler()
    handler.setLevel(effective_levelno)
    handler.addFilter(ContextEnricherFilter())
    handler.addFilter(SensitiveRedactionFilter())
    handler.setFormatter(StructuredFormatter())

    root.handlers.clear()
    root.addHandler(handler)

    # Prevent Alembic double logging
    logging.getLogger("alembic").propagate = False
    logging.getLogger("alembic.runtime.migration").propagate = False

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
