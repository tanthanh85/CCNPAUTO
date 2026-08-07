"""Read and validate managed IOS XE loopbacks from NetBox."""

from __future__ import annotations

import logging
import re
from ipaddress import IPv4Interface

import pynetbox


logger = logging.getLogger(__name__)


class NetBoxSourceError(ValueError):
    """Represent incomplete or unsafe loopback intent in NetBox."""


class NetBoxLoopbackSource:
    LOOPBACK_NAME = re.compile(r"^Loopback(?P<id>\d+)$")
    TAG_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

    def __init__(self, url, token, device_name, tag_slug="automation-managed"):
        if not self.TAG_SLUG.fullmatch(tag_slug):
            raise NetBoxSourceError(
                "NETBOX_TAG must contain a NetBox tag slug such as "
                f"'automation-managed'; received {tag_slug!r}"
            )
        self.device_name = device_name
        self.tag_slug = tag_slug
        self.api = pynetbox.api(url, token=token)
        logger.debug(
            "Initialized NetBox client url=%s device=%s tag=%s "
            "token_configured=%s",
            url,
            device_name,
            tag_slug,
            bool(token),
        )

    def load(self, require_entries=True):
        logger.info(
            "Reading NetBox loopback intent device=%s tag=%s require_entries=%s",
            self.device_name,
            self.tag_slug,
            require_entries,
        )
        device = self.api.dcim.devices.get(name=self.device_name)
        if device is None:
            raise NetBoxSourceError(f"NetBox device not found: {self.device_name}")

        interfaces = list(
            self.api.dcim.interfaces.filter(device_id=device.id, tag=self.tag_slug)
        )
        logger.info(
            "NetBox returned %d tagged interface object(s) device_id=%s",
            len(interfaces),
            device.id,
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
        logger.info("NetBox intent validation passed records=%d", len(loopbacks))
        logger.debug("Normalized NetBox intent=%s", loopbacks)
        return loopbacks

    def _normalize(self, interface):
        logger.debug(
            "Normalizing NetBox interface name=%s id=%s",
            interface.name,
            interface.id,
        )
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
        normalized = {
            "id": int(match.group("id")),
            "description": description,
            "ipv4": str(address.ip),
            "prefix_length": 32,
            "netmask": "255.255.255.255",
            "enabled": bool(interface.enabled),
        }
        logger.debug(
            "Normalized NetBox interface name=%s ipv4=%s enabled=%s",
            interface.name,
            normalized["ipv4"],
            normalized["enabled"],
        )
        return normalized
