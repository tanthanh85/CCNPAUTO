"""Small display helpers for loopback pages and client metrics."""

from __future__ import annotations

from typing import Any

from tabulate import tabulate


def print_interfaces(records: list[dict[str, Any]], title: str) -> None:
    rows = [
        [
            item.get("interface", "-"),
            item.get("ipv4", "unassigned"),
            item.get("admin_status", "unknown"),
            item.get("oper_status", "unknown"),
        ]
        for item in records
    ]
    print(f"\n{title}\n{'=' * len(title)}")
    print(
        tabulate(
            rows,
            headers=["Interface", "IPv4", "Admin", "Operational"],
            tablefmt="github",
        )
    )
