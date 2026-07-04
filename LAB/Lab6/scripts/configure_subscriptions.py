#!/usr/bin/env python3

import json

import requests

from src.payload import build_mdt_payload
from src.restconf import RESTCONFClient
from src.settings import Settings


try:
    settings = Settings()
    settings.confirm_changes()
    payload = build_mdt_payload(
        settings.receiver_ip,
        settings.receiver_port,
        settings.period_cs,
    )
    client = RESTCONFClient(settings)
    response = client.patch_config(payload)
    print(f"RESTCONF PATCH returned HTTP {response.status_code}")
    print(json.dumps(client.get_config(), indent=2))
except PermissionError as error:
    print(f"Safety check stopped configuration: {error}")
except requests.RequestException as error:
    print(f"RESTCONF transport failed: {error}")
except (RuntimeError, ValueError) as error:
    print(f"Configuration stopped: {error}")
