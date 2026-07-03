#!/usr/bin/env python3

from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

from src.iosxe_cli import IOSXEDevice
from src.reporting import print_interfaces, print_version
from src.settings import Settings


device = None

try:
    settings = Settings()
    device = IOSXEDevice(settings)
    device.connect()

    print_version(device.get_version())
    print_interfaces(device.get_interfaces(), "IOS XE Interfaces from CLI and TextFSM")

except NetmikoAuthenticationException:
    print("Authentication failed. Check the sandbox username and password.")
except NetmikoTimeoutException:
    print("Connection timed out. Check the VPN, host, and SSH port.")
except (ValueError, RuntimeError) as error:
    print(f"Collection failed: {error}")
finally:
    if device:
        device.disconnect()
