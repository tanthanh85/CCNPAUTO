#!/usr/bin/env python3

import json

import requests

from src.restconf import RESTCONFClient
from src.settings import Settings


try:
    settings = Settings()
    client = RESTCONFClient(settings)
    print(json.dumps(client.get_operational(), indent=2))
except requests.RequestException as error:
    print(f"RESTCONF transport failed: {error}")
except (RuntimeError, ValueError) as error:
    print(f"State retrieval stopped: {error}")
