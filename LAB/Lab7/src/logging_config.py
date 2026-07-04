"""Structured JSON logging with redaction and separate audit output."""

import json
import logging
import re
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


SENSITIVE_KEY = re.compile(r"password|passwd|secret|token|authorization", re.IGNORECASE)
SENSITIVE_TEXT = re.compile(
    r"(?i)(password|passwd|secret|token|authorization)(\s*[=:]\s*)([^\s,;]+)"
)


def redact(value, key=""):
    if SENSITIVE_KEY.search(str(key)):
        return "***REDACTED***"
    if isinstance(value, dict):
        return {item_key: redact(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_TEXT.sub(r"\1\2***REDACTED***", value)
    return value


class UTCJsonFormatter(logging.Formatter):
    """Convert each LogRecord into one machine-readable JSON object."""

    def format(self, record):
        event = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }

        for field in (
            "event_type",
            "correlation_id",
            "change_id",
            "actor",
            "device",
            "management_ip",
            "command_count",
            "duration_ms",
            "outcome",
            "error_type",
        ):
            if hasattr(record, field):
                event[field] = redact(getattr(record, field), field)

        if record.exc_info:
            event["exception"] = redact(self.formatException(record.exc_info))

        return json.dumps(event, separators=(",", ":"), ensure_ascii=False)


def _handler(path, max_bytes, backups):
    handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backups,
        encoding="utf-8",
    )
    handler.setFormatter(UTCJsonFormatter())
    return handler


def configure_logging(log_level="INFO", max_bytes=1_000_000, backups=3):
    Path("logs").mkdir(exist_ok=True)
    level = getattr(logging, log_level.upper(), logging.INFO)

    application = logging.getLogger("network_automation")
    application.setLevel(level)
    application.handlers.clear()
    application.propagate = False
    application.addHandler(_handler("logs/application.jsonl", max_bytes, backups))

    console = logging.StreamHandler()
    console.setFormatter(UTCJsonFormatter())
    application.addHandler(console)

    audit = logging.getLogger("network_audit")
    audit.setLevel(logging.INFO)
    audit.handlers.clear()
    audit.propagate = False
    audit.addHandler(_handler("logs/audit.jsonl", max_bytes, backups))

    logging.Formatter.converter = time.gmtime
    return application, audit
