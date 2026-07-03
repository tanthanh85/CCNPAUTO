"""A small RESTCONF client for IOS XE interface information."""

import requests
import urllib3


class RESTCONFClient:
    CISCO_PATH = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
    IETF_PATH = "/restconf/data/ietf-interfaces:interfaces-state"

    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = (settings.username, settings.password)
        self.session.headers.update({"Accept": "application/yang-data+json"})
        self.session.verify = settings.verify_tls

        if not settings.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_interfaces(self):
        response = self._get(self.CISCO_PATH)
        if response.status_code == 404:
            response = self._get(self.IETF_PATH)
        response.raise_for_status()
        return response.json()

    def _get(self, path):
        return self.session.get(
            self.settings.base_url + path,
            timeout=30,
        )

    def normalize(self, payload):
        root = payload.get("Cisco-IOS-XE-interfaces-oper:interfaces")
        if root is None:
            root = payload.get("ietf-interfaces:interfaces-state", {})

        interfaces = []
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

            interfaces.append(
                {
                    "interface": item.get("name", "-"),
                    "ip_address": ipv4 or "unassigned",
                    "status": admin,
                    "protocol": protocol,
                }
            )
        return interfaces
