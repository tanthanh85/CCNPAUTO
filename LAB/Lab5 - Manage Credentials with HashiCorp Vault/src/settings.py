"""Cumulative project settings with IOS XE credentials supplied by Vault."""

import logging
import os

from dotenv import load_dotenv

from src.vault_credentials import VaultCredentialProvider


logger = logging.getLogger(__name__)


class Settings:
    def __init__(self):
        load_dotenv()
        self.host = self._required("IOSXE_HOST")
        self.ssh_port = int(os.getenv("IOSXE_SSH_PORT", "22"))
        self.https_port = int(os.getenv("IOSXE_HTTPS_PORT", "443"))
        self.netconf_port = int(os.getenv("IOSXE_NETCONF_PORT", "830"))
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
        logger.debug(
            "Loaded cumulative settings host=%s ssh_port=%d https_port=%d "
            "netconf_port=%d "
            "netbox_url=%s netbox_device=%s netbox_tag=%s "
            "verify_tls=%s vault_credentials_loaded=%s",
            self.host,
            self.ssh_port,
            self.https_port,
            self.netconf_port,
            self.netbox_url,
            self.netbox_device,
            self.netbox_tag,
            self.verify_tls,
            bool(self.username and self.password),
        )

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

    @property
    def base_url(self):
        return f"https://{self.host}:{self.https_port}"
