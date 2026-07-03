#!/usr/bin/env python3

import json
from pathlib import Path

from src.iosxe_restconf import get_interface_data, normalize_interfaces
from src.reporting import print_interfaces
from src.settings import load_settings


settings = load_settings()
payload = get_interface_data(settings)
interfaces = normalize_interfaces(payload)

artifact_folder = Path("artifacts")
artifact_folder.mkdir(exist_ok=True)
(artifact_folder / "interfaces-restconf.json").write_text(json.dumps(payload, indent=2))

print_interfaces(interfaces, "IOS XE Interfaces from RESTCONF JSON")
