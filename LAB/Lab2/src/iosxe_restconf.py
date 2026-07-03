"""Simple RESTCONF functions for IOS XE interface data."""

import requests
import urllib3


CISCO_PATH = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
IETF_PATH = "/restconf/data/ietf-interfaces:interfaces-state"


def get_interface_data(settings):
    base_url = f"https://{settings['host']}:{settings['https_port']}"
    headers = {"Accept": "application/yang-data+json"}
    authentication = (settings["username"], settings["password"])

    if not settings["verify_tls"]:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = requests.get(
        base_url + CISCO_PATH,
        headers=headers,
        auth=authentication,
        verify=settings["verify_tls"],
        timeout=30,
    )

    if response.status_code == 404:
        response = requests.get(
            base_url + IETF_PATH,
            headers=headers,
            auth=authentication,
            verify=settings["verify_tls"],
            timeout=30,
        )

    response.raise_for_status()
    return response.json()


def normalize_interfaces(payload):
    root = payload.get("Cisco-IOS-XE-interfaces-oper:interfaces")
    if root is None:
        root = payload.get("ietf-interfaces:interfaces-state", {})

    normalized = []
    for item in root.get("interface", []):
        ipv4 = item.get("ipv4", item.get("ietf-ip:ipv4", "unassigned"))
        if isinstance(ipv4, dict):
            addresses = ipv4.get("address", [])
            ipv4 = addresses[0].get("ip", "unassigned") if addresses else "unassigned"

        admin = str(item.get("admin-status", "unknown")).replace("if-state-", "")
        protocol = str(item.get("oper-status", "unknown")).replace(
            "if-oper-state-", ""
        )
        if protocol == "ready":
            protocol = "up"

        normalized.append(
            {
                "interface": item.get("name", "-"),
                "ip_address": ipv4 or "unassigned",
                "status": admin,
                "protocol": protocol,
            }
        )

    return normalized
