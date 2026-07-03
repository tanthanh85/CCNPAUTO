"""Normalize and select IOS XE interface records."""

from __future__ import annotations

import re
from typing import Any


INTERFACES_PATH = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
INTERFACE_PATH = INTERFACES_PATH + "/interface={name}"
LOOPBACK_PATTERN = re.compile(r"^Loopback(?P<identifier>\d+)$")


def _state(value: Any, prefixes: tuple[str, ...]) -> str:
    text = str(value or "unknown")
    for prefix in prefixes:
        text = text.removeprefix(prefix)
    text = text.replace("-state", "").replace("-oper", "")
    return "up" if text == "ready" else text


def _entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    root = payload.get("Cisco-IOS-XE-interfaces-oper:interfaces")
    if isinstance(root, dict):
        result = root.get("interface", [])
        return result if isinstance(result, list) else [result]

    detail = payload.get("Cisco-IOS-XE-interfaces-oper:interface")
    if isinstance(detail, list):
        return detail
    if isinstance(detail, dict):
        return [detail]
    raise ValueError("Unexpected IOS XE interface response structure")


def normalize_interfaces(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for entry in _entries(payload):
        records.append(
            {
                "interface": entry.get("name", "-"),
                "ipv4": entry.get("ipv4") or "unassigned",
                "admin_status": _state(entry.get("admin-status"), ("if-state-",)),
                "oper_status": _state(
                    entry.get("oper-status"),
                    ("if-oper-state-", "if-oper-"),
                ),
            }
        )
    return records


def select_lab_loopbacks(
    records: list[dict[str, Any]], start_id: int = 1001, count: int = 100
) -> list[dict[str, Any]]:
    end_id = start_id + count - 1
    selected = []
    for record in records:
        match = LOOPBACK_PATTERN.fullmatch(str(record["interface"]))
        if match and start_id <= int(match.group("identifier")) <= end_id:
            selected.append(record)
    return sorted(
        selected,
        key=lambda item: int(LOOPBACK_PATTERN.fullmatch(item["interface"])["identifier"]),
    )
