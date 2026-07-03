"""Lab 3 settings loaded from .env."""

import os

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()

        host = self._required("IOSXE_HOST")
        port = int(os.getenv("IOSXE_HTTPS_PORT", "443"))

        self.base_url = f"https://{host}:{port}"
        self.username = self._required("IOSXE_USERNAME")
        self.password = self._required("IOSXE_PASSWORD")
        self.verify_tls = os.getenv("VERIFY_TLS", "false").lower() == "true"
        self.requests_per_second = float(os.getenv("REQUESTS_PER_SECOND", "5"))
        self.connect_timeout = float(os.getenv("IOSXE_CONNECT_TIMEOUT", "10"))
        self.read_timeout = float(os.getenv("IOSXE_READ_TIMEOUT", "45"))
        self.max_retries = int(os.getenv("IOSXE_MAX_RETRIES", "3"))
        self.burst_max_requests = int(os.getenv("BURST_MAX_REQUESTS", "200"))
        self.burst_max_seconds = float(os.getenv("BURST_MAX_SECONDS", "30"))
        self.burst_max_backoffs = int(os.getenv("BURST_MAX_BACKOFFS", "3"))

        if self.requests_per_second <= 0:
            raise ValueError("REQUESTS_PER_SECOND must be greater than zero")
        if self.max_retries < 0:
            raise ValueError("IOSXE_MAX_RETRIES cannot be negative")
        if self.burst_max_requests <= 0 or self.burst_max_seconds <= 0:
            raise ValueError("Burst request and duration limits must be greater than zero")
        if self.burst_max_backoffs < 0:
            raise ValueError("BURST_MAX_BACKOFFS cannot be negative")

    @staticmethod
    def _required(name):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in the .env file")
        return value
