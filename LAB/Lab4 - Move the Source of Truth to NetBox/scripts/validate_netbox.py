#!/usr/bin/env python3
"""Validate the complete NetBox loopback source of truth without changing IOS XE."""

import logging
from pathlib import Path

from src.logging_config import configure_logging
from src.netbox_source import NetBoxLoopbackSource, NetBoxSourceError
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main():
    configure_logging("validate_netbox", project_root=ROOT)
    logger.info("Starting read-only NetBox validation")
    settings = Settings()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    loopbacks = source.load()
    logger.info("Validated %d managed NetBox loopback(s)", len(loopbacks))
    logger.debug("Validated NetBox loopback records=%s", loopbacks)
    for item in loopbacks:
        print(
            f"Loopback{item['id']}: {item['ipv4']}/{item['prefix_length']} "
            f"enabled={item['enabled']}"
        )
    print(f"PASS: NetBox contains {len(loopbacks)} valid managed loopback(s).")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, NetBoxSourceError) as exc:
        logger.exception("NetBox source validation failed")
        raise SystemExit(f"FAIL: {exc}") from exc
