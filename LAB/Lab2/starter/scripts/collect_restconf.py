#!/usr/bin/env python3
"""Collect IOS XE interface state from RESTCONF JSON and print a table."""

import json
from pathlib import Path

from src.iosxe_restconf import IOSXERESTCONFClient, normalize_interfaces
from src.reporting import print_interfaces
from src.settings import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = Settings.from_env()
    client = IOSXERESTCONFClient(settings)
    payload = client.get_interfaces_payload()

    artifact_dir = PROJECT_ROOT / "artifacts"
    artifact_dir.mkdir(exist_ok=True)
    artifact_path = artifact_dir / "interfaces-restconf.json"
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    interfaces = normalize_interfaces(payload)
    print_interfaces(interfaces, "IOS XE Interfaces from RESTCONF JSON")
    print(f"\nRaw JSON saved to {artifact_path}")


if __name__ == "__main__":
    main()
