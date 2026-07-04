"""A small RESTCONF client for Cisco IOS XE native OSPF configuration."""

import requests
import urllib3


ROUTER_PATH = "/restconf/data/Cisco-IOS-XE-native:native/router"


class RESTCONFClient:
    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = (settings.username, settings.password)
        self.session.verify = settings.verify_tls
        self.session.headers.update(
            {
                "Accept": "application/yang-data+json",
                "Content-Type": "application/yang-data+json",
            }
        )
        if not settings.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def patch_ospf(self, payload):
        response = self.session.patch(
            self.settings.restconf_url + ROUTER_PATH,
            json=payload,
            timeout=(10, 60),
        )
        self._check(response)
        return response

    def get_ospf(self):
        path = ROUTER_PATH + "/Cisco-IOS-XE-ospf:router-ospf/ospf"
        response = self.session.get(
            self.settings.restconf_url + path,
            timeout=(10, 60),
        )
        self._check(response)
        return response.json()

    @staticmethod
    def _check(response):
        if response.status_code not in (200, 201, 204):
            raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
