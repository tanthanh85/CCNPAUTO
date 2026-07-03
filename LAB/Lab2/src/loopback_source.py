"""Validate loopback source-of-truth data and render IOS XE commands."""

from __future__ import annotations

import json
from ipaddress import IPv4Interface
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from yaml.constructor import ConstructorError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "loopbacks.schema.json"


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _format_error(error: ValidationError) -> str:
    location = ".".join(str(part) for part in error.absolute_path)
    return f"{location or '<document>'}: {error.message}"


def load_loopbacks(
    path: Path,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    *,
    require_entries: bool = True,
) -> list[dict[str, Any]]:
    """Load YAML, enforce its schema, and apply cross-record validation."""
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if data is None:
        data = {}

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda item: list(item.path))
    if errors:
        details = "\n  - ".join(_format_error(error) for error in errors)
        raise ValueError(f"Source-of-truth schema validation failed:\n  - {details}")

    loopbacks = data.get("loopbacks")
    if require_entries and not loopbacks:
        raise ValueError(
            "data/loopbacks.yaml must contain a nonempty loopbacks list; "
            "add the lab loopback on your feature branch"
        )

    validated: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_ips: set[str] = set()

    for item in loopbacks:
        loopback_id = int(item["id"])
        if loopback_id in seen_ids:
            raise ValueError(f"Duplicate Loopback ID: {loopback_id}")

        address = IPv4Interface(f"{item['ipv4']}/{int(item['prefix_length'])}")
        if str(address.ip) in seen_ips:
            raise ValueError(f"Duplicate Loopback IPv4 address: {address.ip}")

        description = item["description"].strip()

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
