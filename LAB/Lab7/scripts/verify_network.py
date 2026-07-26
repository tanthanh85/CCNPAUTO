#!/usr/bin/env python3
"""Verify loopback addresses and OSPF configuration against NetBox intent."""

import logging
from pathlib import Path

from src.iosxe_cli import IOSXEDevice
from src.iosxe_netconf import IOSXENETCONF
from src.logging_config import configure_logging
from src.netbox_source import NetBoxLoopbackSource
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main():
    configure_logging("verify_network", project_root=ROOT)
    logger.info("Starting end-to-end NetBox, IOS XE, and OSPF verification")
    settings = Settings()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    intended = source.load()
    logger.info("Loaded %d intended loopback(s) from NetBox", len(intended))
    logger.debug("Intended loopbacks=%s", intended)

    cli = IOSXEDevice(settings)
    try:
        cli.connect()
        observed = {item["interface"]: item for item in cli.get_interfaces()}
        logger.info("Collected %d observed IOS XE interface(s)", len(observed))
    finally:
        cli.disconnect()

    ospf_xml = IOSXENETCONF(settings).get_ospf_config()
    logger.debug("Observed running OSPF XML=%s", ospf_xml)
    errors = []
    for item in intended:
        name = f"Loopback{item['id']}"
        state = observed.get(name)
        logger.debug(
            "Verifying interface=%s expected_ip=%s observed=%s ospf_present=%s",
            name,
            item["ipv4"],
            state,
            item["ipv4"] in ospf_xml,
        )
        if not state or state["ip_address"] != item["ipv4"]:
            errors.append(f"{name} does not match NetBox address {item['ipv4']}")
        if item["ipv4"] not in ospf_xml:
            errors.append(f"{name} address {item['ipv4']} is absent from OSPF")
    if errors:
        logger.error("End-to-end verification failures=%s", errors)
        raise RuntimeError("; ".join(errors))
    logger.info("End-to-end verification passed loopbacks=%d", len(intended))
    print(f"PASS: {len(intended)} NetBox loopback(s) match IOS XE and OSPF area 0.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        logger.exception("End-to-end network verification failed")
        raise SystemExit(f"Verification failed: {exc}") from exc
