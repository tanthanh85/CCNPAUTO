#!/usr/bin/env python3
"""Validate the complete NetBox loopback source of truth without changing IOS XE."""

from src.netbox_source import NetBoxLoopbackSource, NetBoxSourceError
from src.settings import Settings


def main():
    settings = Settings()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    loopbacks = source.load()
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
        raise SystemExit(f"FAIL: {exc}") from exc

