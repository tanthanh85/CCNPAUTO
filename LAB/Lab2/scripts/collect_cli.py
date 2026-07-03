#!/usr/bin/env python3
"""Collect and tabulate IOS XE CLI data through Netmiko and TextFSM."""

from src.iosxe_cli import IOSXECLIClient
from src.reporting import print_interfaces, print_version
from src.settings import Settings


def main() -> None:
    settings = Settings.from_env()
    with IOSXECLIClient(settings) as device:
        version_records = device.collect_version()
        interface_records = device.collect_interfaces()

    print_version(version_records)
    print_interfaces(interface_records, "IOS XE Interfaces from CLI and TextFSM")


if __name__ == "__main__":
    main()
