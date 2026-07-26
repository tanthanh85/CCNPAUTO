#!/usr/bin/env python3
"""Configure OSPF area 0 for every NetBox-managed loopback through NETCONF."""

import logging
import os
from pathlib import Path

from ncclient.operations import RPCError
from ncclient.transport.errors import AuthenticationError, SSHError

from src.iosxe_netconf import IOSXENETCONF
from src.logging_config import configure_logging
from src.netbox_source import NetBoxLoopbackSource
from src.ospf_renderer import OSPFRenderer
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main():
    configure_logging("configure_ospf", project_root=ROOT)
    logger.info("Starting NETCONF OSPF reconciliation")
    settings = Settings()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    loopbacks = source.load()
    process_id = os.getenv("OSPF_PROCESS_ID", "1")
    area = os.getenv("OSPF_AREA", "0")
    logger.info(
        "Loaded %d loopback(s) for OSPF process_id=%s area=%s",
        len(loopbacks),
        process_id,
        area,
    )
    payload = OSPFRenderer().render(
        loopbacks,
        process_id=process_id,
        area=area,
    )
    logger.debug("Rendered NETCONF OSPF payload=%s", payload)
    print("Rendered NETCONF payload:\n")
    print(payload)

    client = IOSXENETCONF(settings)
    print("\nNETCONF edit-config reply:")
    edit_reply = client.configure_ospf(payload)
    logger.debug("NETCONF edit-config reply=%s", edit_reply)
    print(edit_reply)
    running = client.get_ospf_config()
    logger.debug("NETCONF running OSPF data=%s", running)
    print("\nRunning OSPF configuration returned by NETCONF:")
    print(running)

    missing = [item["ipv4"] for item in loopbacks if item["ipv4"] not in running]
    if missing:
        logger.error("OSPF verification missing_addresses=%s", missing)
        raise RuntimeError(f"OSPF verification is missing: {', '.join(missing)}")
    logger.info("OSPF verification passed loopbacks=%d", len(loopbacks))
    print(f"PASS: OSPF area 0 contains all {len(loopbacks)} managed loopback(s).")


if __name__ == "__main__":
    try:
        main()
    except AuthenticationError as exc:
        logger.exception("NETCONF authentication failed")
        raise SystemExit("NETCONF authentication failed") from exc
    except SSHError as exc:
        logger.exception("NETCONF SSH connection failed")
        raise SystemExit(f"NETCONF SSH connection failed: {exc}") from exc
    except RPCError as exc:
        logger.exception("IOS XE rejected NETCONF payload")
        raise SystemExit(f"IOS XE rejected the NETCONF payload: {exc}") from exc
    except (ValueError, RuntimeError) as exc:
        logger.exception("OSPF configuration failed")
        raise SystemExit(f"OSPF configuration failed: {exc}") from exc
