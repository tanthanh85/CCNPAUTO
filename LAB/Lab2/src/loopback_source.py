"""Load, validate, and render the loopback source of truth."""

from ipaddress import IPv4Interface
from pathlib import Path

import yaml
from jinja2 import Template


class LoopbackManager:
    REQUIRED_FIELDS = {"id", "description", "ipv4", "prefix_length", "enabled"}

    def __init__(self, yaml_path, template_path):
        self.yaml_path = Path(yaml_path)
        self.template_path = Path(template_path)

    def load(self, require_entries=True):
        data = yaml.safe_load(self.yaml_path.read_text()) or {}

        if not isinstance(data, dict) or set(data) != {"loopbacks"}:
            raise ValueError("The YAML file must contain only the 'loopbacks' key")
        if not isinstance(data["loopbacks"], list):
            raise ValueError("loopbacks must be a YAML list")
        if require_entries and not data["loopbacks"]:
            raise ValueError("Add at least one loopback to data/loopbacks.yaml")

        validated = []
        seen_ids = set()
        seen_ips = set()

        for position, item in enumerate(data["loopbacks"], start=1):
            loopback = self._validate_item(item, position)

            if loopback["id"] in seen_ids:
                raise ValueError(f"Duplicate Loopback ID: {loopback['id']}")
            if loopback["ipv4"] in seen_ips:
                raise ValueError(f"Duplicate Loopback IPv4 address: {loopback['ipv4']}")

            seen_ids.add(loopback["id"])
            seen_ips.add(loopback["ipv4"])
            validated.append(loopback)

        return validated

    def _validate_item(self, item, position):
        if not isinstance(item, dict) or set(item) != self.REQUIRED_FIELDS:
            raise ValueError(
                f"Item {position} must use these fields: {sorted(self.REQUIRED_FIELDS)}"
            )
        if type(item["id"]) is not int or item["id"] < 0:
            raise ValueError(f"Item {position}: id must be a positive integer")
        if type(item["prefix_length"]) is not int:
            raise ValueError(f"Item {position}: prefix_length must be an integer")
        if type(item["enabled"]) is not bool:
            raise ValueError(f"Item {position}: enabled must be true or false")
        if not isinstance(item["description"], str) or not item["description"].strip():
            raise ValueError(f"Item {position}: description is required")
        if "\n" in item["description"] or "\r" in item["description"]:
            raise ValueError(f"Item {position}: description must be one line")

        address = IPv4Interface(f"{item['ipv4']}/{item['prefix_length']}")
        return {
            "id": item["id"],
            "description": item["description"].strip(),
            "ipv4": str(address.ip),
            "netmask": str(address.network.netmask),
            "enabled": item["enabled"],
        }

    def render(self, loopback):
        template = Template(self.template_path.read_text())
        rendered = template.render(loopback=loopback)
        return [line.strip() for line in rendered.splitlines() if line.strip()]
