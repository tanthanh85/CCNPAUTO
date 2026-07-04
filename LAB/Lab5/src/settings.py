"""Cumulative project settings with IOS XE credentials supplied by Vault."""

import os

from dotenv import load_dotenv

from src.vault_credentials import VaultCredentialProvider


class Settings:
    def __init__(self):
        load_dotenv()
        self.host = self._required("IOSXE_HOST")
        self.ssh_port = int(os.getenv("IOSXE_SSH_PORT", "22"))
        self.https_port = int(os.getenv("IOSXE_HTTPS_PORT", "443"))
        self.sandbox_mode = os.getenv("SANDBOX_MODE", "")
        self.allow_changes = self._boolean("ALLOW_CONFIG_CHANGES", False)
        self.verify_tls = self._boolean("VERIFY_TLS", False)

        self.netbox_url = self._required("NETBOX_URL")
        self.netbox_token = self._required("NETBOX_TOKEN")
        self.netbox_device = os.getenv("NETBOX_DEVICE", "iosxe-sandbox")
        self.netbox_tag = os.getenv("NETBOX_TAG", "automation-managed")

        provider = VaultCredentialProvider(
            address=os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"),
            mount_point=os.getenv("VAULT_MOUNT", "secret"),
            secret_path=os.getenv("VAULT_IOSXE_PATH", "ccnpauto/iosxe"),
        )
        self.username, self.password = provider.read_iosxe()

    @staticmethod
    def _required(name):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in .env")
        return value

    @staticmethod
    def _boolean(name, default):
        value = os.getenv(name, str(default)).lower()
        if value in {"true", "yes", "1"}:
            return True
        if value in {"false", "no", "0"}:
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

