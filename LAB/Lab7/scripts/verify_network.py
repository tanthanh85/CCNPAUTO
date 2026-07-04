#!/usr/bin/env python3
"""Verify loopback addresses and OSPF configuration against NetBox intent."""

from src.iosxe_cli import IOSXEDevice
from src.iosxe_netconf import IOSXENETCONF
from src.netbox_source import NetBoxLoopbackSource
from src.settings import Settings


def main():
    settings = Settings()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    intended = source.load()

    cli = IOSXEDevice(settings)
    try:
        cli.connect()
        observed = {item["interface"]: item for item in cli.get_interfaces()}
    finally:
        cli.disconnect()

    ospf_xml = IOSXENETCONF(settings).get_ospf_config()
    errors = []
    for item in intended:
        name = f"Loopback{item['id']}"
        state = observed.get(name)
        if not state or state["ip_address"] != item["ipv4"]:
            errors.append(f"{name} does not match NetBox address {item['ipv4']}")
        if item["ipv4"] not in ospf_xml:
            errors.append(f"{name} address {item['ipv4']} is absent from OSPF")
    if errors:
        raise RuntimeError("; ".join(errors))
    print(f"PASS: {len(intended)} NetBox loopback(s) match IOS XE and OSPF area 0.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"Verification failed: {exc}") from exc

