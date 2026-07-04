"""Load and validate Lab 5 environment settings."""

import os

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()
        self.host = self._required("IOSXE_HOST")
        self.netconf_port = int(os.getenv("IOSXE_NETCONF_PORT", "830"))
        self.restconf_port = int(os.getenv("IOSXE_RESTCONF_PORT", "443"))
        self.username = self._required("IOSXE_USERNAME")
        self.password = self._required("IOSXE_PASSWORD")
        self.verify_tls = os.getenv("VERIFY_TLS", "false").lower() == "true"
        self.start_id = int(os.getenv("LOOPBACK_START_ID", "501"))
        self.count = int(os.getenv("LOOPBACK_COUNT", "10"))
        self.address_prefix = os.getenv("LOOPBACK_ADDRESS_PREFIX", "198.18.10")
        self.ospf_process_id = int(os.getenv("OSPF_PROCESS_ID", "10"))
        self.allow_changes = os.getenv("ALLOW_CONFIG_CHANGES", "false").lower() == "true"

        if self.count != 10:
            raise ValueError("This lab requires LOOPBACK_COUNT=10")
        if not 1 <= self.ospf_process_id <= 65535:
            raise ValueError("OSPF_PROCESS_ID must be from 1 through 65535")
        octets = self.address_prefix.split(".")
        if len(octets) != 3 or any(not item.isdigit() for item in octets):
            raise ValueError("LOOPBACK_ADDRESS_PREFIX must contain three IPv4 octets")

    @property
    def restconf_url(self):
        return f"https://{self.host}:{self.restconf_port}"

    def loopbacks(self):
        return [
            {
                "id": self.start_id + offset,
                "name": f"Loopback{self.start_id + offset}",
                "address": f"{self.address_prefix}.{offset + 1}",
                "prefix_length": 32,
                "description": "LAB5_IETF_NETCONF",
            }
            for offset in range(self.count)
        ]

    def confirm_changes(self):
        if not self.allow_changes:
            raise PermissionError("Set ALLOW_CONFIG_CHANGES=true after reviewing the payload")

    @staticmethod
    def _required(name):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in .env")
        return value
