"""RESTCONF client for IOS XE telemetry configuration and state."""

import requests
import urllib3


CONFIG_PATH = "/restconf/data/Cisco-IOS-XE-mdt-cfg:mdt-config-data"
OPER_PATH = "/restconf/data/Cisco-IOS-XE-mdt-oper:mdt-oper-data"


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

    def patch_config(self, payload):
        response = self.session.patch(
            self.settings.base_url + CONFIG_PATH,
            json=payload,
            timeout=(10, 60),
        )
        self._check(response)
        return response

    def get_config(self):
        response = self.session.get(
            self.settings.base_url + CONFIG_PATH,
            timeout=(10, 60),
        )
        self._check(response)
        return response.json()

    def get_operational(self):
        response = self.session.get(
            self.settings.base_url + OPER_PATH,
            timeout=(10, 60),
        )
        self._check(response)
        return response.json()

    def delete_subscription(self, subscription_id):
        path = f"{CONFIG_PATH}/mdt-subscription={subscription_id}"
        response = self.session.delete(
            self.settings.base_url + path,
            timeout=(10, 60),
        )
        if response.status_code not in (204, 404):
            self._check(response)
        return response.status_code

    def delete_receiver(self, receiver_name):
        path = (
            f"{CONFIG_PATH}/mdt-named-protocol-rcvrs/"
            f"mdt-named-protocol-rcvr={receiver_name}"
        )
        response = self.session.delete(
            self.settings.base_url + path,
            timeout=(10, 60),
        )
        if response.status_code not in (204, 404):
            self._check(response)
        return response.status_code

    @staticmethod
    def _check(response):
        if response.status_code not in (200, 201, 204):
            raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
