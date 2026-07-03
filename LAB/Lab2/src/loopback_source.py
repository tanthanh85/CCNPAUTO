"""Read, validate, and render the loopback YAML file."""

from ipaddress import IPv4Interface
from pathlib import Path

import yaml
from jinja2 import Template


def load_loopbacks(path, require_entries=True):
    data = yaml.safe_load(Path(path).read_text()) or {}
    if not isinstance(data, dict) or set(data) != {"loopbacks"}:
        raise ValueError("The YAML file must contain only the 'loopbacks' key")

    loopbacks = data["loopbacks"]
    if not isinstance(loopbacks, list):
        raise ValueError("loopbacks must be a YAML list")
    if require_entries and not loopbacks:
        raise ValueError("Add at least one loopback to data/loopbacks.yaml")

    fields = {"id", "description", "ipv4", "prefix_length", "enabled"}
    validated = []
    seen_ids = set()
    seen_ips = set()

    for position, item in enumerate(loopbacks, start=1):
        if not isinstance(item, dict) or set(item) != fields:
            raise ValueError(f"Item {position} must use these fields: {sorted(fields)}")
        if type(item["id"]) is not int:
            raise ValueError(f"Item {position}: id must be an integer")
        if item["id"] < 0:
            raise ValueError(f"Item {position}: id cannot be negative")
        if type(item["prefix_length"]) is not int:
            raise ValueError(f"Item {position}: prefix_length must be an integer")
        if type(item["enabled"]) is not bool:
            raise ValueError(f"Item {position}: enabled must be true or false")
        if not isinstance(item["description"], str) or not item["description"].strip():
            raise ValueError(f"Item {position}: description is required")
        if "\n" in item["description"] or "\r" in item["description"]:
            raise ValueError(f"Item {position}: description must be one line")

        loopback_id = item["id"]
        if loopback_id in seen_ids:
            raise ValueError(f"Duplicate Loopback ID: {loopback_id}")

        address = IPv4Interface(f"{item['ipv4']}/{item['prefix_length']}")
        if str(address.ip) in seen_ips:
            raise ValueError(f"Duplicate Loopback IPv4 address: {address.ip}")

        validated.append(
            {
                "id": loopback_id,
                "description": item["description"].strip(),
                "ipv4": str(address.ip),
                "netmask": str(address.network.netmask),
                "enabled": item["enabled"],
            }
        )
        seen_ids.add(loopback_id)
        seen_ips.add(str(address.ip))

    return validated


def render_commands(loopback, template_dir):
    template_text = (Path(template_dir) / "loopback.j2").read_text()
    rendered = Template(template_text).render(loopback=loopback)
    return [line.strip() for line in rendered.splitlines() if line.strip()]
