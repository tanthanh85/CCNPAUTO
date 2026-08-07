#!/usr/bin/env python3

import json
from pathlib import Path

import requests

from src.iosxe_restconf import RESTCONFClient
from src.reporting import print_interfaces
from src.settings import Settings


try:
    client = RESTCONFClient(Settings())
    payload = client.get_interfaces()
    interfaces = client.normalize(payload)

    artifact_folder = Path("artifacts")
    artifact_folder.mkdir(exist_ok=True)
    output_file = artifact_folder / "interfaces-restconf.json"
    output_file.write_text(json.dumps(payload, indent=2))

    print_interfaces(interfaces, "IOS XE Interfaces from RESTCONF JSON")

except requests.Timeout:
    print("RESTCONF timed out. Check the VPN and HTTPS address.")
except requests.HTTPError as error:
    print(f"RESTCONF returned an HTTP error: {error}")
except requests.RequestException as error:
    print(f"RESTCONF connection failed: {error}")
except (ValueError, json.JSONDecodeError) as error:
    print(f"The response could not be processed: {error}")
