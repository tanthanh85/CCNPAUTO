#!/usr/bin/env python3
"""Inventory FMC and manage one lab-owned network object."""

from __future__ import annotations

import argparse
import csv
import ipaddress
import os
from pathlib import Path

from tabulate import tabulate

from fmc_client import FMCClient, FMCError


def lab_settings() -> tuple[str, str, bool]:
    name = os.getenv("LAB_OBJECT_NAME", "LAB15-NETWORK").strip()
    value = os.getenv("LAB_OBJECT_VALUE", "198.18.15.0/24").strip()
    allow = os.getenv("ALLOW_FMC_CHANGES", "false").lower() == "true"
    if not name.startswith("LAB15-"):
        raise FMCError("LAB_OBJECT_NAME must begin with LAB15-")
    try:
        ipaddress.ip_network(value, strict=True)
    except ValueError as exc:
        raise FMCError(f"LAB_OBJECT_VALUE must be a canonical network: {exc}") from exc
    return name, value, allow


def one_lab_object(client: FMCClient, name: str) -> dict | None:
    matches = [item for item in client.network_objects(name) if item.get("name") == name]
    if len(matches) > 1:
        raise FMCError(f"More than one object is named {name}; stop and inspect FMC")
    return matches[0] if matches else None


def inventory(client: FMCClient) -> None:
    version = client.server_version()
    print("FMC server information")
    print(version)

    devices = client.devices()
    print("\nManaged devices")
    print(
        tabulate(
            [
                [d.get("name"), d.get("hostName"), d.get("model"), d.get("healthStatus"), d.get("id")]
                for d in devices
            ],
            headers=["Name", "Host", "Model", "Health", "ID"],
        )
    )

    policies = client.access_policies()
    print("\nAccess control policies")
    print(tabulate([[p.get("name"), p.get("id")] for p in policies], headers=["Name", "ID"]))


def rules(client: FMCClient, policy_id: str) -> None:
    entries = client.access_rules(policy_id)
    rows = []
    for rule in entries:
        rows.append(
            [
                rule.get("metadata", {}).get("ruleIndex"),
                rule.get("name"),
                rule.get("action"),
                rule.get("enabled"),
                rule.get("logBegin"),
                rule.get("logEnd"),
                rule.get("id"),
            ]
        )
    print(tabulate(rows, headers=["Index", "Name", "Action", "Enabled", "Log begin", "Log end", "ID"]))


def export_rules(client: FMCClient, policy_id: str) -> None:
    entries = client.access_rules(policy_id)
    output = Path("output/access_rules.csv")
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("index", "name", "action", "enabled", "log_begin", "log_end", "id"),
        )
        writer.writeheader()
        for rule in entries:
            writer.writerow(
                {
                    "index": rule.get("metadata", {}).get("ruleIndex"),
                    "name": rule.get("name"),
                    "action": rule.get("action"),
                    "enabled": rule.get("enabled"),
                    "log_begin": rule.get("logBegin"),
                    "log_end": rule.get("logEnd"),
                    "id": rule.get("id"),
                }
            )
    print(f"Exported {len(entries)} rules to {output}")


def require_changes(allow: bool) -> None:
    if not allow:
        raise FMCError("Set ALLOW_FMC_CHANGES=true only after reviewing the requested operation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("inventory", "rules", "export-rules", "show-object", "create-object", "update-object", "delete-object"),
    )
    parser.add_argument("--policy-id", default=os.getenv("FMC_ACCESS_POLICY_ID", ""))
    parser.add_argument("--new-value", help="new canonical network for update-object")
    args = parser.parse_args()

    client = FMCClient()
    name, value, allow = lab_settings()
    if args.action == "inventory":
        inventory(client)
    elif args.action in {"rules", "export-rules"}:
        if not args.policy_id:
            raise FMCError("Set FMC_ACCESS_POLICY_ID or supply --policy-id")
        rules(client, args.policy_id) if args.action == "rules" else export_rules(client, args.policy_id)
    else:
        current = one_lab_object(client, name)
        if args.action == "show-object":
            print(current or f"{name} does not exist")
        elif args.action == "create-object":
            require_changes(allow)
            if current:
                raise FMCError(f"{name} already exists with ID {current['id']}")
            print(client.create_network(name, value))
        elif args.action == "update-object":
            require_changes(allow)
            if not current:
                raise FMCError(f"{name} does not exist")
            new_value = args.new_value or value
            ipaddress.ip_network(new_value, strict=True)
            print(client.update_network(current["id"], current, new_value))
        elif args.action == "delete-object":
            require_changes(allow)
            if not current:
                print(f"{name} is already absent")
            else:
                client.delete_network(current["id"])
                print(f"Deleted {name} ({current['id']})")


if __name__ == "__main__":
    try:
        main()
    except (FMCError, ValueError) as exc:
        raise SystemExit(f"Lab error: {exc}") from exc

