#!/usr/bin/env python3
"""Reconcile NetBox-managed loopbacks to the reserved IOS XE router."""

from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

from src.iosxe_cli import IOSXEDevice
from src.loopback_renderer import LoopbackRenderer
from src.netbox_source import NetBoxLoopbackSource
from src.reporting import print_interfaces
from src.settings import Settings


def main():
    settings = Settings()
    settings.confirm_write_access()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    loopbacks = source.load()
    commands = LoopbackRenderer().render(loopbacks)

    device = IOSXEDevice(settings)
    try:
        device.connect()
        print(device.configure(commands))
        observed = device.get_interfaces()
        print_interfaces(observed, "Interfaces After NetBox Reconciliation")
    finally:
        device.disconnect()

    actual = {item["interface"]: item for item in observed}
    errors = []
    for intent in loopbacks:
        name = f"Loopback{intent['id']}"
        state = actual.get(name)
        if state is None:
            errors.append(f"{name} is missing")
        elif state["ip_address"] != intent["ipv4"]:
            errors.append(f"{name} expected {intent['ipv4']}, got {state['ip_address']}")
        elif intent["enabled"] and (state["status"], state["protocol"]) != ("up", "up"):
            errors.append(f"{name} is not up/up")
    if errors:
        raise RuntimeError("; ".join(errors))
    print(f"PASS: reconciled and verified {len(loopbacks)} loopback(s).")


if __name__ == "__main__":
    try:
        main()
    except PermissionError as exc:
        raise SystemExit(f"Safety check stopped the change: {exc}") from exc
    except NetmikoAuthenticationException as exc:
        raise SystemExit("IOS XE authentication failed") from exc
    except NetmikoTimeoutException as exc:
        raise SystemExit("IOS XE connection timed out") from exc
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"Reconciliation failed: {exc}") from exc

