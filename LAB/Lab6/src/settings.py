"""Load Lab 6 settings from the local environment file."""

import ipaddress
import os

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()
        self.host = self._required("IOSXE_HOST")
        self.restconf_port = int(os.getenv("IOSXE_RESTCONF_PORT", "443"))
        self.username = self._required("IOSXE_USERNAME")
        self.password = self._required("IOSXE_PASSWORD")
        self.verify_tls = os.getenv("VERIFY_TLS", "false").lower() == "true"
        self.receiver_ip = str(
            ipaddress.ip_address(self._required("TELEMETRY_RECEIVER_IP"))
        )
        self.receiver_port = int(os.getenv("TELEMETRY_RECEIVER_PORT", "57000"))
        self.period_cs = int(os.getenv("TELEMETRY_PERIOD_CS", "1000"))
        self.allow_changes = os.getenv("ALLOW_CONFIG_CHANGES", "false").lower() == "true"

        if not 1 <= self.receiver_port <= 65535:
            raise ValueError("TELEMETRY_RECEIVER_PORT is invalid")
        if self.period_cs < 100:
            raise ValueError("Use a period of at least 100 centiseconds")

    @property
    def base_url(self):
        return f"https://{self.host}:{self.restconf_port}"

    def confirm_changes(self):
        if not self.allow_changes:
            raise PermissionError("Set ALLOW_CONFIG_CHANGES=true after payload review")

    @staticmethod
    def _required(name):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in .env")
        return value
