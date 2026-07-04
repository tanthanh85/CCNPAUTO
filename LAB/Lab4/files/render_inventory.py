#!/usr/bin/env python3
"""Render a compact device table from the training inventory."""

from pathlib import Path

import yaml
from tabulate import tabulate


def load_devices(path):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    devices = data.get("devices", [])
    if not isinstance(devices, list):
        raise ValueError("devices must be a YAML list")
    if not devices:
        raise ValueError("inventory must contain at least one device")
    return devices


def main():
    devices = load_devices("network_inventory.yaml")
    rows = [
        [item["hostname"], item["platform"], item["role"], item["management_ip"]]
        for item in devices
    ]
    print(tabulate(rows, headers=["Hostname", "Platform", "Role", "Management IP"]))


if __name__ == "__main__":
    main()
