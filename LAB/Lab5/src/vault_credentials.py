"""Retrieve IOS XE login credentials from HashiCorp Vault KV v2."""

import logging
import os
from pathlib import Path

import hvac


logger = logging.getLogger(__name__)


class VaultCredentialError(RuntimeError):
    """Represent missing Vault authentication or secret data."""


class VaultCredentialProvider:
    def __init__(self, address, mount_point="secret", secret_path="ccnpauto/iosxe"):
        token_file = Path.home() / ".vault-token"
        token = os.getenv("VAULT_TOKEN")
        if not token and token_file.exists():
            token = token_file.read_text(encoding="utf-8").strip()
        self.client = hvac.Client(url=address, token=token)
        self.mount_point = mount_point
        self.secret_path = secret_path
        logger.debug(
            "Initialized Vault client address=%s mount_point=%s "
            "secret_path=%s token_configured=%s",
            address,
            mount_point,
            secret_path,
            bool(token),
        )

    def read_iosxe(self):
        logger.info(
            "Reading IOS XE credential from Vault mount_point=%s secret_path=%s",
            self.mount_point,
            self.secret_path,
        )
        if not self.client.is_authenticated():
            logger.error("Vault authentication check failed")
            raise VaultCredentialError(
                "Vault authentication failed. Run 'vault login' before the script."
            )
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point,
                path=self.secret_path,
                raise_on_deleted_version=True,
            )
            data = response["data"]["data"]
            username = str(data["username"]).strip()
            password = str(data["password"])
        except (KeyError, TypeError, hvac.exceptions.VaultError) as exc:
            raise VaultCredentialError(
                f"Could not read username/password from {self.mount_point}/{self.secret_path}"
            ) from exc
        if not username or not password:
            raise VaultCredentialError("Vault returned an empty IOS XE username or password")
        logger.info(
            "Vault credential retrieved username_present=%s password_present=%s",
            bool(username),
            bool(password),
        )
        return username, password
