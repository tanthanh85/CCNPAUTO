#!/usr/bin/env python3

from src.iosxe_cli import connect, get_interfaces, get_version
from src.reporting import print_interfaces, print_version
from src.settings import load_settings


settings = load_settings()
connection = connect(settings)

try:
    version = get_version(connection)
    interfaces = get_interfaces(connection)
finally:
    connection.disconnect()

print_version(version)
print_interfaces(interfaces, "IOS XE Interfaces from CLI and TextFSM")
