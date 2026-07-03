"""Reusable Netmiko client for IOS XE CLI collection and configuration."""

from __future__ import annotations

from typing import Any

from netmiko import ConnectHandler

from src.settings import Settings


class IOSXECLIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.connection: Any | None = None

    def __enter__(self) -> "IOSXECLIClient":
        self.connection = ConnectHandler(
            device_type="cisco_ios",
            host=self.settings.host,
            port=self.settings.ssh_port,
            username=self.settings.username,
            password=self.settings.password,
            conn_timeout=20,
            auth_timeout=20,
            banner_timeout=30,
            fast_cli=False,
        )
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.connection is not None:
            self.connection.disconnect()

    def _send_structured(self, command: str) -> list[dict[str, Any]]:
        if self.connection is None:
            raise RuntimeError("Use IOSXECLIClient as a context manager")
        result = self.connection.send_command(command, use_textfsm=True)
        if isinstance(result, str):
            raise RuntimeError(
                f"TextFSM did not parse {command!r}. The raw output began with: "
                f"{result[:160]!r}"
            )
        return result

    def collect_version(self) -> list[dict[str, Any]]:
        return self._send_structured("show version")

    def collect_interfaces(self) -> list[dict[str, Any]]:
        records = self._send_structured("show ip interface brief")
        return [
            {
                "interface": row.get("interface", "-"),
                "ip_address": row.get("ip_address", "unassigned"),
                "status": row.get("status", "unknown"),
                "protocol": row.get("proto", row.get("protocol", "unknown")),
            }
            for row in records
        ]

    def send_config(self, commands: list[str]) -> str:
        self.settings.require_reserved_write_access()
        if self.connection is None:
            raise RuntimeError("Use IOSXECLIClient as a context manager")
        return self.connection.send_config_set(commands)
