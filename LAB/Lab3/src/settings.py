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

        if self.requests_per_second <= 0:
            raise ValueError("REQUESTS_PER_SECOND must be greater than zero")
        if self.max_retries < 0:
            raise ValueError("IOSXE_MAX_RETRIES cannot be negative")

    @staticmethod
    def _required(name):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in the .env file")
        return value
