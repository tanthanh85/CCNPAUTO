#!/usr/bin/env python3
"""Collect and print IOS XE interface status, or use safe demo data."""

import os

from netmiko import ConnectHandler
from tabulate import tabulate


class InterfaceCollector:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    def collect(self):
        if self.demo_mode:
            return [
                {"interface": "GigabitEthernet1", "ip_address": "192.0.2.10", "status": "up", "protocol": "up"},
                {"interface": "Loopback100", "ip_address": "198.51.100.100", "status": "up", "protocol": "up"},
            ]

        required = ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise ValueError(f"Missing runtime settings: {', '.join(missing)}")

        device = {
            "device_type": "cisco_ios",
            "host": os.environ["IOSXE_HOST"],
            "port": int(os.getenv("IOSXE_SSH_PORT", "22")),
            "username": os.environ["IOSXE_USERNAME"],
            "password": os.environ["IOSXE_PASSWORD"],
        }
        connection = None
        try:
            connection = ConnectHandler(**device)
            result = connection.send_command("show ip interface brief", use_textfsm=True)
            if not isinstance(result, list):
                raise RuntimeError("TextFSM did not return structured interface records")
            return result
        finally:
            if connection:
                connection.disconnect()


def main():
    try:
        records = InterfaceCollector().collect()
        rows = [
            [
                item.get("interface") or item.get("intf"),
                item.get("ip_address") or item.get("ipaddr"),
                item.get("status"),
                item.get("protocol") or item.get("proto"),
            ]
            for item in records
        ]
        print(tabulate(rows, headers=["Interface", "IP Address", "Status", "Protocol"], tablefmt="rounded_grid"))
    except Exception as error:
        print(f"Collection failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
