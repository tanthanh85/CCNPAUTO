from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from src.vault_credentials import get_iosxe_credentials_from_vault


load_dotenv()


@dataclass(frozen=True)
class IosXeSettings:
    host: str
    netconf_port: int
    restconf_port: int
    username: str
    password: str
    verify_tls: bool

    @property
    def restconf_base_url(self) -> str:
        return f"https://{self.host}:{self.restconf_port}/restconf/data"


def load_settings() -> IosXeSettings:
    use_vault = os.getenv("USE_VAULT", "false").lower() == "true"

    if use_vault:
        credentials = get_iosxe_credentials_from_vault()
        username = credentials["username"]
        password = credentials["password"]
    else:
        username = os.getenv("IOSXE_USERNAME", "")
        password = os.getenv("IOSXE_PASSWORD", "")

    return IosXeSettings(
        host=os.getenv("IOSXE_HOST", ""),
        netconf_port=int(os.getenv("IOSXE_NETCONF_PORT", "830")),
        restconf_port=int(os.getenv("IOSXE_RESTCONF_PORT", "443")),
        username=username,
        password=password,
        verify_tls=os.getenv("IOSXE_VERIFY_TLS", "true").lower() == "true",
    )

