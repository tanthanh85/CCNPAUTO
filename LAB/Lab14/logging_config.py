"""Logging configuration for the standalone AI route assistant."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


class SecretRedactionFilter(logging.Filter):
    SECRET_MARKERS = ("PASSWORD", "TOKEN", "SECRET", "API_KEY", "PRIVATE_KEY")

    def __init__(self) -> None:
        super().__init__()
        self.secret_values = {
            value
            for name, value in os.environ.items()
            if value
            and len(value) >= 4
            and any(marker in name.upper() for marker in self.SECRET_MARKERS)
        }

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for value in self.secret_values:
            message = message.replace(value, "[REDACTED]")
        record.msg = message
        record.args = ()
        return True


def _as_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


def _level(name: str, default: str) -> int:
    value = os.getenv(name, default).strip().upper()
    level = getattr(logging, value, None)
    if not isinstance(level, int):
        raise ValueError(
            f"{name} must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
        )
    return level


def configure_logging(application_name: str) -> Path | None:
    load_dotenv()
    root = Path(__file__).resolve().parent
    log_dir = Path(os.getenv("LOG_DIR", "logs")).expanduser()
    if not log_dir.is_absolute():
        log_dir = root / log_dir

    enable_file = _as_bool("ENABLE_FILE_LOGGING", False)
    enable_console = _as_bool("ENABLE_CONSOLE_LOGGING", True)
    file_level = _level("LOG_LEVEL", "DEBUG")
    console_level = _level("LOG_CONSOLE_LEVEL", "INFO")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    for handler in list(root_logger.handlers):
        if getattr(handler, "_ccnpauto_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    redaction_filter = SecretRedactionFilter()

    if enable_console:
        console = logging.StreamHandler()
        console.setLevel(console_level)
        console.setFormatter(formatter)
        console.addFilter(redaction_filter)
        console._ccnpauto_handler = True
        root_logger.addHandler(console)

    log_path: Path | None = None
    if enable_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = "".join(
            character if character.isalnum() or character in "-_" else "_"
            for character in application_name
        )
        log_path = log_dir / f"{safe_name}_{timestamp}.log"
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redaction_filter)
        file_handler._ccnpauto_handler = True
        root_logger.addHandler(file_handler)

    logging.getLogger(__name__).info(
        "Logging initialized application=%s file_logging=%s file_level=%s "
        "console_logging=%s console_level=%s log_file=%s",
        application_name,
        enable_file,
        logging.getLevelName(file_level),
        enable_console,
        logging.getLevelName(console_level),
        log_path or "disabled",
    )
    return log_path
