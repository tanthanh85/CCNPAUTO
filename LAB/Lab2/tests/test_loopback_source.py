from pathlib import Path

import pytest
import yaml

from src.loopback_source import load_loopbacks


def write_source(tmp_path: Path, loopbacks: list[dict]) -> Path:
    path = tmp_path / "loopbacks.yaml"
    path.write_text(yaml.safe_dump({"loopbacks": loopbacks}), encoding="utf-8")
    return path


def loopback(interface_id: int, address: str) -> dict:
    return {
        "id": interface_id,
        "description": f"LAB2_LOOPBACK_{interface_id}",
        "ipv4": address,
        "prefix_length": 32,
        "enabled": True,
    }


def test_accepts_one_loopback(tmp_path: Path) -> None:
    result = load_loopbacks(write_source(tmp_path, [loopback(101, "192.0.2.101")]))
    assert result[0]["netmask"] == "255.255.255.255"


def test_accepts_multiple_loopbacks(tmp_path: Path) -> None:
    source = [
        loopback(101, "192.0.2.101"),
        loopback(102, "192.0.2.102"),
        loopback(103, "192.0.2.103"),
    ]
    assert len(load_loopbacks(write_source(tmp_path, source))) == 3


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "101"),
        ("ipv4", "999.0.2.101"),
        ("prefix_length", 33),
        ("enabled", "yes"),
    ],
)
def test_rejects_wrong_field_types_or_values(
    tmp_path: Path, field: str, value: object
) -> None:
    record = loopback(101, "192.0.2.101")
    record[field] = value
    with pytest.raises(ValueError, match="schema validation failed"):
        load_loopbacks(write_source(tmp_path, [record]))


def test_rejects_unknown_fields(tmp_path: Path) -> None:
    record = loopback(101, "192.0.2.101")
    record["subnet_mask"] = "255.255.255.255"
    with pytest.raises(ValueError, match="Additional properties"):
        load_loopbacks(write_source(tmp_path, [record]))


def test_rejects_duplicate_ids(tmp_path: Path) -> None:
    source = [
        loopback(101, "192.0.2.101"),
        loopback(101, "192.0.2.102"),
    ]
    with pytest.raises(ValueError, match="Duplicate Loopback ID"):
        load_loopbacks(write_source(tmp_path, source))


def test_rejects_duplicate_addresses(tmp_path: Path) -> None:
    source = [
        loopback(101, "192.0.2.101"),
        loopback(102, "192.0.2.101"),
    ]
    with pytest.raises(ValueError, match="Duplicate Loopback IPv4"):
        load_loopbacks(write_source(tmp_path, source))


def test_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    path = tmp_path / "loopbacks.yaml"
    path.write_text(
        """---
loopbacks:
  - id: 101
    id: 102
    description: LAB2_DUPLICATE_KEY
    ipv4: 192.0.2.101
    prefix_length: 32
    enabled: true
""",
        encoding="utf-8",
    )
    with pytest.raises(yaml.constructor.ConstructorError, match="duplicate key"):
        load_loopbacks(path)
