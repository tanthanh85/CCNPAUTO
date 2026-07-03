"""Load and validate connection settings without storing secrets in Git."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("REPLACE_WITH_"):
        raise ValueError(f"Set {name} in the untracked .env file")
    return value


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false, not {value!r}")


@dataclass(frozen=True)
class Settings:
    host: str
    ssh_port: int
    https_port: int
    username: str
    password: str
    sandbox_mode: str
    allow_config_changes: bool
    verify_tls: bool

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        mode = os.getenv("SANDBOX_MODE", "always-on").strip().lower()
        if mode not in {"always-on", "reserved"}:
            raise ValueError("SANDBOX_MODE must be always-on or reserved")

        return cls(
            host=_required("IOSXE_HOST"),
            ssh_port=int(os.getenv("IOSXE_SSH_PORT", "22")),
            https_port=int(os.getenv("IOSXE_HTTPS_PORT", "443")),
            username=_required("IOSXE_USERNAME"),
            password=_required("IOSXE_PASSWORD"),
            sandbox_mode=mode,
            allow_config_changes=_as_bool("ALLOW_CONFIG_CHANGES"),
            verify_tls=_as_bool("VERIFY_TLS"),
        )

    def require_reserved_write_access(self) -> None:
        if self.sandbox_mode != "reserved":
            raise PermissionError(
                "Configuration is blocked: reserve an IOS XE sandbox and set "
                "SANDBOX_MODE=reserved"
            )
        if not self.allow_config_changes:
            raise PermissionError(
                "Configuration is blocked: set ALLOW_CONFIG_CHANGES=true only "
                "after confirming that the reservation belongs to you"
            )
