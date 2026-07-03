#!/usr/bin/env python3

import json
import requests

from src.http_cache import HTTPCache
from src.restconf_client import APIError, RESTCONFClient
from src.settings import Settings


PATH = "/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback?content=config"

try:
    client = RESTCONFClient(Settings())
    cache = HTTPCache(".cache/loopbacks.json")
    response = client.get_response(PATH, headers=cache.conditional_headers())

    print("HTTP status:", response.status_code)
    print("Cache-Control:", response.headers.get("Cache-Control", "<absent>"))
    print("ETag:", response.headers.get("ETag", "<absent>"))
    print("Last-Modified:", response.headers.get("Last-Modified", "<absent>"))

    if response.status_code == 304:
        print("The resource did not change. The saved payload can be reused.")
    elif response.status_code == 200:
        payload = response.json()
        if cache.save(payload, response.headers):
            print("Saved the payload and HTTP validator for the next run.")
        else:
            print("No usable validator was returned. Nothing was cached.")
    else:
        client._raise_for_status(response, PATH)

except requests.Timeout:
    print("The optional cache request timed out.")
except requests.ConnectionError as error:
    print(f"Could not connect to RESTCONF: {error}")
except (APIError, ValueError, json.JSONDecodeError, requests.JSONDecodeError) as error:
    print(f"The cache exercise could not complete: {error}")
