#!/usr/bin/env python3
"""Reconcile NetBox-managed loopbacks to the reserved IOS XE router."""

import logging
from pathlib import Path

from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

from src.iosxe_cli import IOSXEDevice
from src.logging_config import configure_logging
from src.loopback_renderer import LoopbackRenderer
from src.netbox_source import NetBoxLoopbackSource
from src.reporting import print_interfaces
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main():
    configure_logging("sync_loopbacks_from_netbox", project_root=ROOT)
    logger.info("Starting NetBox-to-IOS-XE loopback reconciliation")
    settings = Settings()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    loopbacks = source.load()
    logger.info("Loaded %d managed loopback(s) from NetBox", len(loopbacks))
    logger.debug("Normalized NetBox loopback intent=%s", loopbacks)
    commands = LoopbackRenderer().render(loopbacks)
    logger.info("Rendered %d IOS XE configuration command(s)", len(commands))
    logger.debug("Proposed IOS XE commands=%s", commands)

    device = IOSXEDevice(settings)
    try:
        device.connect()
        response = device.configure(commands)
        logger.debug("IOS XE configuration response=%s", response)
        print(response)
        observed = device.get_interfaces()
        logger.info("Collected %d observed interface record(s)", len(observed))
        print_interfaces(observed, "Interfaces After NetBox Reconciliation")
    finally:
        device.disconnect()

    actual = {item["interface"]: item for item in observed}
    errors = []
    for intent in loopbacks:
        name = f"Loopback{intent['id']}"
        state = actual.get(name)
        logger.debug(
            "Verifying NetBox intent interface=%s expected_ip=%s "
            "expected_enabled=%s observed=%s",
            name,
            intent["ipv4"],
            intent["enabled"],
            state,
        )
        if state is None:
            errors.append(f"{name} is missing")
        elif state["ip_address"] != intent["ipv4"]:
            errors.append(f"{name} expected {intent['ipv4']}, got {state['ip_address']}")
        elif intent["enabled"] and (state["status"], state["protocol"]) != ("up", "up"):
            errors.append(f"{name} is not up/up")
    if errors:
        logger.error("Reconciliation verification failures=%s", errors)
        raise RuntimeError("; ".join(errors))
    logger.info("Reconciliation verified loopbacks=%d", len(loopbacks))
    print(f"PASS: reconciled and verified {len(loopbacks)} loopback(s).")


if __name__ == "__main__":
    try:
        main()
    except NetmikoAuthenticationException as exc:
        logger.exception("IOS XE authentication failed")
        raise SystemExit("IOS XE authentication failed") from exc
    except NetmikoTimeoutException as exc:
        logger.exception("IOS XE connection timed out")
        raise SystemExit("IOS XE connection timed out") from exc
    except (ValueError, RuntimeError) as exc:
        logger.exception("NetBox reconciliation failed")
        raise SystemExit(f"Reconciliation failed: {exc}") from exc
