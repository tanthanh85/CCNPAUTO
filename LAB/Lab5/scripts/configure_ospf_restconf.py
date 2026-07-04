#!/usr/bin/env python3

import json

import requests

from src.payloads import build_ospf_router_payload
from src.restconf_client import RESTCONFClient
from src.settings import Settings


try:
    settings = Settings()
    settings.confirm_changes()
    loopbacks = settings.loopbacks()
    payload = build_ospf_router_payload(loopbacks, settings.ospf_process_id)

    client = RESTCONFClient(settings)
    response = client.patch_ospf(payload)
    print(f"RESTCONF OSPF PATCH returned HTTP {response.status_code}")

    observed = client.get_ospf()
    print(json.dumps(observed, indent=2))

except PermissionError as error:
    print(f"Safety check stopped configuration: {error}")
except requests.RequestException as error:
    print(f"RESTCONF connection failed: {error}")
except (RuntimeError, ValueError) as error:
    print(f"Workflow stopped: {error}")
