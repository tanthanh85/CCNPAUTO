"""Functions that normalize, select, and display interface records."""

import re

from tabulate import tabulate


def normalize_interfaces(payload):
    root = payload.get("Cisco-IOS-XE-interfaces-oper:interfaces")
    if root is not None:
        items = root.get("interface", [])
    else:
        items = payload.get("Cisco-IOS-XE-interfaces-oper:interface", [])

    if isinstance(items, dict):
        items = [items]

    interfaces = []
    for item in items:
        admin = str(item.get("admin-status", "unknown")).replace("if-state-", "")
        operational = str(item.get("oper-status", "unknown")).replace(
            "if-oper-state-", ""
        )
        if operational == "ready":
            operational = "up"

        interfaces.append(
            {
                "interface": item.get("name", "-"),
                "ipv4": item.get("ipv4") or "unassigned",
                "admin": admin,
                "operational": operational,
            }
        )
    return interfaces


def select_lab_loopbacks(interfaces):
    selected = []

    for interface in interfaces:
        match = re.fullmatch(r"Loopback(\d+)", interface["interface"])
        if match and 1001 <= int(match.group(1)) <= 1100:
            selected.append(interface)

    return sorted(selected, key=lambda item: int(item["interface"].replace("Loopback", "")))


def print_interfaces(interfaces, title):
    rows = []
    for item in interfaces:
        rows.append(
            [item["interface"], item["ipv4"], item["admin"], item["operational"]]
        )

    print(f"\n{title}")
    print(
        tabulate(
            rows,
            headers=["Interface", "IPv4", "Admin", "Operational"],
            tablefmt="github",
        )
    )
