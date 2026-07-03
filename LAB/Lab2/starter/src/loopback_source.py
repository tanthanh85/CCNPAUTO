"""Validate loopback source-of-truth data and render IOS XE commands."""

from __future__ import annotations

from ipaddress import IPv4Interface
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def load_loopbacks(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    loopbacks = data.get("loopbacks")
    if not isinstance(loopbacks, list) or not loopbacks:
        raise ValueError(
            "data/loopbacks.yaml must contain a nonempty loopbacks list; "
            "add the lab loopback on your feature branch"
        )

    validated: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_ips: set[str] = set()

    for item in loopbacks:
        if not isinstance(item, dict):
            raise ValueError("Each loopback entry must be a mapping")
        required = {"id", "description", "ipv4", "prefix_length", "enabled"}
        missing = required - item.keys()
        if missing:
            raise ValueError(f"Loopback entry is missing: {sorted(missing)}")

        loopback_id = int(item["id"])
        if not 0 <= loopback_id <= 2147483647:
            raise ValueError(f"Invalid Loopback ID: {loopback_id}")
        if loopback_id in seen_ids:
            raise ValueError(f"Duplicate Loopback ID: {loopback_id}")

        address = IPv4Interface(f"{item['ipv4']}/{int(item['prefix_length'])}")
        if str(address.ip) in seen_ips:
            raise ValueError(f"Duplicate Loopback IPv4 address: {address.ip}")

        description = str(item["description"]).strip()
        if not description or "\n" in description or "\r" in description:
            raise ValueError("Description must be one nonempty line")
        if not isinstance(item["enabled"], bool):
            raise ValueError("enabled must be the YAML Boolean true or false")

        validated.append(
            {
                "id": loopback_id,
                "description": description,
                "ipv4": str(address.ip),
                "prefix_length": address.network.prefixlen,
                "netmask": str(address.network.netmask),
                "enabled": item["enabled"],
            }
        )
        seen_ids.add(loopback_id)
        seen_ips.add(str(address.ip))

    return validated


def render_commands(loopback: dict[str, Any], template_dir: Path) -> list[str]:
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    rendered = environment.get_template("loopback.j2").render(loopback=loopback)
    return [line.strip() for line in rendered.splitlines() if line.strip()]
