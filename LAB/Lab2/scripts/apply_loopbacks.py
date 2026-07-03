#!/usr/bin/env python3

from pathlib import Path

import yaml
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

from src.iosxe_cli import IOSXEDevice
from src.loopback_source import LoopbackManager
from src.reporting import print_interfaces
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
device = None

try:
    settings = Settings()
    settings.confirm_write_access()

    manager = LoopbackManager(
        ROOT / "data" / "loopbacks.yaml",
        ROOT / "templates" / "loopback.j2",
    )
    loopbacks = manager.load()

    device = IOSXEDevice(settings)
    device.connect()

    print_interfaces(device.get_interfaces(), "Interfaces Before the Change")

    commands = manager.render(loopbacks)
    print(f"Applying {len(loopbacks)} loopback interface(s)")
    print(device.configure(commands))

    after = device.get_interfaces()
    print_interfaces(after, "Interfaces After the Change")

    observed = {item["interface"]: item for item in after}
    errors = []

    for loopback in loopbacks:
        name = f"Loopback{loopback['id']}"
        actual = observed.get(name)

        if actual is None:
            errors.append(f"{name} is missing")
        elif actual["ip_address"] != loopback["ipv4"]:
            errors.append(f"{name} has the wrong IP address")
        elif loopback["enabled"] and (
            actual["status"] != "up" or actual["protocol"] != "up"
        ):
            errors.append(f"{name} is not up/up")

    if errors:
        raise RuntimeError("; ".join(errors))

    print("Verification passed.")

except PermissionError as error:
    print(f"Safety check stopped the change: {error}")
except yaml.YAMLError as error:
    print(f"The YAML file is not valid: {error}")
except NetmikoAuthenticationException:
    print("Authentication failed. No configuration was sent.")
except NetmikoTimeoutException:
    print("Connection timed out. Check the VPN and reservation details.")
except (ValueError, RuntimeError) as error:
    print(f"The change failed: {error}")
finally:
    if device:
        device.disconnect()
