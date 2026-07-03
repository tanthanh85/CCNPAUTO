"""Read connection values from the untracked .env file."""

import os

from dotenv import load_dotenv


def load_settings():
    load_dotenv()

    for name in ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD"]:
        value = os.getenv(name, "")
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in the .env file")

    return {
        "host": os.getenv("IOSXE_HOST"),
        "ssh_port": int(os.getenv("IOSXE_SSH_PORT", "22")),
        "https_port": int(os.getenv("IOSXE_HTTPS_PORT", "443")),
        "username": os.getenv("IOSXE_USERNAME"),
        "password": os.getenv("IOSXE_PASSWORD"),
        "sandbox_mode": os.getenv("SANDBOX_MODE", ""),
        "allow_changes": os.getenv("ALLOW_CONFIG_CHANGES", "false").lower()
        == "true",
        "verify_tls": os.getenv("VERIFY_TLS", "false").lower() == "true",
    }


def confirm_write_access(settings):
    if settings["sandbox_mode"] != "reserved":
        raise PermissionError("SANDBOX_MODE must be reserved")
    if not settings["allow_changes"]:
        raise PermissionError("Set ALLOW_CONFIG_CHANGES=true before configuration")
