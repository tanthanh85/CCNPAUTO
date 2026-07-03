"""Validated Lab 3 settings loaded from an untracked .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("REPLACE_WITH_"):
        raise ValueError(f"Set {name} in the untracked .env file")
    return value


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


@dataclass(frozen=True)
class Settings:
    host: str
    https_port: int
    username: str
    password: str
    verify_tls: bool
    requests_per_second: float
    connect_timeout: float
    read_timeout: float
    max_retries: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        settings = cls(
            host=_required("IOSXE_HOST"),
            https_port=int(os.getenv("IOSXE_HTTPS_PORT", "443")),
            username=_required("IOSXE_USERNAME"),
            password=_required("IOSXE_PASSWORD"),
            verify_tls=_boolean("VERIFY_TLS", False),
            requests_per_second=float(os.getenv("REQUESTS_PER_SECOND", "5")),
            connect_timeout=float(os.getenv("IOSXE_CONNECT_TIMEOUT", "10")),
            read_timeout=float(os.getenv("IOSXE_READ_TIMEOUT", "45")),
            max_retries=int(os.getenv("IOSXE_MAX_RETRIES", "3")),
        )
        if settings.requests_per_second <= 0:
            raise ValueError("REQUESTS_PER_SECOND must be greater than zero")
        if settings.connect_timeout <= 0 or settings.read_timeout <= 0:
            raise ValueError("HTTP timeouts must be greater than zero")
        if not 0 <= settings.max_retries <= 10:
            raise ValueError("IOSXE_MAX_RETRIES must be between 0 and 10")
        return settings

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.https_port}"
