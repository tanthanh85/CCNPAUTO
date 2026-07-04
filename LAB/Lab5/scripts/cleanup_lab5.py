#!/usr/bin/env python3

import requests
from ncclient.operations import RPCError

from src.netconf_client import NETCONFClient
from src.payloads import build_netconf_interfaces
from src.settings import Settings


client = None

try:
    settings = Settings()
    settings.confirm_changes()

    ospf_path = (
        "/restconf/data/Cisco-IOS-XE-native:native/router/"
        "Cisco-IOS-XE-ospf:router-ospf/ospf/process-id="
        f"{settings.ospf_process_id}"
    )
    response = requests.delete(
        settings.restconf_url + ospf_path,
        auth=(settings.username, settings.password),
        headers={"Accept": "application/yang-data+json"},
        verify=settings.verify_tls,
        timeout=(10, 60),
    )
    if response.status_code not in (204, 404):
        raise RuntimeError(f"OSPF cleanup failed: HTTP {response.status_code} {response.text}")
    print(f"OSPF cleanup returned HTTP {response.status_code}")

    client = NETCONFClient(settings)
    client.connect()
    payload = build_netconf_interfaces(settings.loopbacks(), operation="delete")
    reply = client.edit_interfaces(payload)
    print(f"Loopback cleanup accepted: {reply.ok}")

except (RPCError, requests.RequestException, RuntimeError, ValueError) as error:
    print(f"Cleanup stopped: {error}")
finally:
    if client:
        client.close()
