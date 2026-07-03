"""Normalize and print tabular CLI and RESTCONF results."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from tabulate import tabulate


def print_records(
    records: Iterable[Mapping[str, Any]],
    columns: list[tuple[str, str]],
    title: str,
) -> None:
    """Print selected dictionary keys using stable display headings."""
    rows = list(records)
    print(f"\n{title}")
    print("=" * len(title))
    if not rows:
        print("No records returned")
        return

    headers = [heading for heading, _ in columns]
    table_rows = [[row.get(key, "-") for _, key in columns] for row in rows]
    print(tabulate(table_rows, headers=headers, tablefmt="github"))


def print_version(records: list[dict[str, Any]]) -> None:
    columns = [
        ("Hostname", "hostname"),
        ("IOS XE Version", "version"),
        ("Image", "running_image"),
        ("Uptime", "uptime"),
        ("Serial", "serial"),
    ]
    normalized = []
    for record in records:
        serial = record.get("serial", "-")
        if isinstance(serial, list):
            serial = ", ".join(serial)
        normalized.append({**record, "serial": serial})
    print_records(normalized, columns, "IOS XE Software and Platform")


def print_interfaces(records: list[dict[str, Any]], title: str) -> None:
    columns = [
        ("Interface", "interface"),
        ("IPv4 Address", "ip_address"),
        ("Admin Status", "status"),
        ("Protocol", "protocol"),
    ]
    print_records(records, columns, title)
