"""Read and validate managed IOS XE loopbacks from NetBox."""

from __future__ import annotations

import re
from ipaddress import IPv4Interface

import pynetbox


class NetBoxSourceError(ValueError):
    """Represent incomplete or unsafe loopback intent in NetBox."""


class NetBoxLoopbackSource:
    LOOPBACK_NAME = re.compile(r"^Loopback(?P<id>\d+)$")

    def __init__(self, url, token, device_name, tag_slug="automation-managed"):
        self.device_name = device_name
        self.tag_slug = tag_slug
        self.api = pynetbox.api(url, token=token)

    def load(self, require_entries=True):
        device = self.api.dcim.devices.get(name=self.device_name)
        if device is None:
            raise NetBoxSourceError(f"NetBox device not found: {self.device_name}")

        interfaces = list(
            self.api.dcim.interfaces.filter(device_id=device.id, tag=self.tag_slug)
        )
        loopbacks = [self._normalize(interface) for interface in interfaces]
        loopbacks.sort(key=lambda item: item["id"])

        if require_entries and not loopbacks:
            raise NetBoxSourceError(
                f"No interfaces tagged '{self.tag_slug}' exist on {self.device_name}"
            )
        ids = [item["id"] for item in loopbacks]
        addresses = [item["ipv4"] for item in loopbacks]
        if len(ids) != len(set(ids)):
            raise NetBoxSourceError("NetBox contains duplicate managed Loopback IDs")
        if len(addresses) != len(set(addresses)):
            raise NetBoxSourceError("NetBox contains duplicate managed IPv4 addresses")
        return loopbacks

    def _normalize(self, interface):
        match = self.LOOPBACK_NAME.fullmatch(interface.name)
        if not match:
            raise NetBoxSourceError(
                f"Tagged interface '{interface.name}' must be named Loopback<number>"
            )
        interface_type = getattr(interface.type, "value", interface.type)
        if str(interface_type) != "virtual":
            raise NetBoxSourceError(f"{interface.name} must use NetBox type Virtual")

        addresses = list(
            self.api.ipam.ip_addresses.filter(interface_id=interface.id, family=4)
        )
        if len(addresses) != 1:
            raise NetBoxSourceError(
                f"{interface.name} must have exactly one assigned IPv4 address"
            )
        address = IPv4Interface(str(addresses[0].address))
        if address.network.prefixlen != 32:
            raise NetBoxSourceError(f"{interface.name} must use an IPv4 /32")

        description = (interface.description or "NETBOX_MANAGED").strip()
        if "\n" in description or "\r" in description:
            raise NetBoxSourceError(f"{interface.name} description must be one line")
        return {
            "id": int(match.group("id")),
            "description": description,
            "ipv4": str(address.ip),
            "prefix_length": 32,
            "netmask": "255.255.255.255",
            "enabled": bool(interface.enabled),
        }
