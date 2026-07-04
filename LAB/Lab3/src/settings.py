"""Application settings loaded from the untracked .env file."""

import os

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()

        self.host = self._required("IOSXE_HOST")
        self.username = self._required("IOSXE_USERNAME")
        self.password = self._required("IOSXE_PASSWORD")
        self.ssh_port = int(os.getenv("IOSXE_SSH_PORT", "22"))
        self.https_port = int(os.getenv("IOSXE_HTTPS_PORT", "443"))
        self.sandbox_mode = os.getenv("SANDBOX_MODE", "")
        self.allow_changes = self._boolean("ALLOW_CONFIG_CHANGES", False)
        self.verify_tls = self._boolean("VERIFY_TLS", False)

    @staticmethod
    def _required(name):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in the .env file")
        return value

    @staticmethod
    def _boolean(name, default):
        value = os.getenv(name, str(default)).lower()
        if value in ["true", "yes", "1"]:
            return True
        if value in ["false", "no", "0"]:
            return False
        raise ValueError(f"{name} must be true or false")

    def confirm_write_access(self):
        if self.sandbox_mode != "reserved":
            raise PermissionError("SANDBOX_MODE must be reserved")
        if not self.allow_changes:
            raise PermissionError("Set ALLOW_CONFIG_CHANGES=true before configuration")

    @property
    def base_url(self):
        return f"https://{self.host}:{self.https_port}"
