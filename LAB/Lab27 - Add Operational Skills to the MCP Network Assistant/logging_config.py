from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


class SecretRedactionFilter(logging.Filter):
    """Remove configured secrets from messages before they reach a handler."""

    MARKERS = ("PASSWORD", "TOKEN", "SECRET", "API_KEY", "PRIVATE_KEY")

    def __init__(self) -> None:
        super().__init__()
        self.values = {
            value
            for name, value in os.environ.items()
            if value
            and len(value) >= 4
            and any(marker in name.upper() for marker in self.MARKERS)
        }

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for value in self.values:
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
        raise ValueError(f"{name} contains an invalid log level")
    return level


def configure_logging(application_name: str) -> Path | None:
    load_dotenv()
    root = Path(__file__).resolve().parent
    log_dir = Path(os.getenv("LOG_DIR", "logs")).expanduser()
    if not log_dir.is_absolute():
        log_dir = root / log_dir

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    for handler in list(root_logger.handlers):
        if getattr(handler, "_lab27_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    redaction = SecretRedactionFilter()

    if _as_bool("ENABLE_CONSOLE_LOGGING", True):
        console = logging.StreamHandler()
        console.setLevel(_level("LOG_CONSOLE_LEVEL", "INFO"))
        console.setFormatter(formatter)
        console.addFilter(redaction)
        console._lab27_handler = True
        root_logger.addHandler(console)

    path: Path | None = None
    if _as_bool("ENABLE_FILE_LOGGING", True):
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
        path = log_dir / f"{application_name}_{timestamp}.log"
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setLevel(_level("LOG_LEVEL", "DEBUG"))
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redaction)
        file_handler._lab27_handler = True
        root_logger.addHandler(file_handler)

    # The lab's own INFO/DEBUG events show the useful agent and tool flow.
    # Protocol libraries are deliberately quieter because their wire-level
    # messages otherwise obscure that flow and FastMCP may add a Rich handler.
    for name in ("mcp", "httpcore", "httpx", "urllib3", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialized application=%s log_file=%s",
        application_name,
        path or "disabled",
    )
    return path
