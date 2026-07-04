"""NetBox intent, Vault credentials, device access, and audit logging."""

import ipaddress
import json
import logging
import os
import re
import time
from pathlib import Path

import hvac
import pynetbox
from netmiko import ConnectHandler


LOOPBACK_PATTERN = re.compile(r"^Loopback(9\d{2})$")
DESCRIPTION_PATTERN = re.compile(r"^[A-Za-z0-9_. -]{1,80}$")
LAB_PREFIX = ipaddress.ip_network("198.18.90.0/24")


def configure_logging(filename):
    Path("artifacts").mkdir(exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S"
    )
    formatter.converter = time.gmtime
    handlers = [logging.FileHandler(f"artifacts/{filename}"), logging.StreamHandler()]
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


def netbox_client():
    url = os.environ.get("NETBOX_URL")
    token = os.environ.get("NETBOX_TOKEN")
    if not url or not token:
        raise ValueError("NETBOX_URL and NETBOX_TOKEN are required")
    return pynetbox.api(url, token=token)


def collect_intent(device_name):
    nb = netbox_client()
    device = nb.dcim.devices.get(name=device_name)
    if not device:
        raise ValueError(f"NetBox device not found: {device_name}")

    desired = []
    seen_ids = set()
    seen_addresses = set()
    for interface in nb.dcim.interfaces.filter(device_id=device.id):
        match = LOOPBACK_PATTERN.fullmatch(interface.name)
        if not match:
            continue
        addresses = list(
            nb.ipam.ip_addresses.filter(
                assigned_object_type="dcim.interface",
                assigned_object_id=interface.id,
            )
        )
        if not addresses:
            addresses = list(nb.ipam.ip_addresses.filter(interface_id=interface.id))
        if len(addresses) != 1:
            raise ValueError(f"{interface.name} must have exactly one assigned IP address")
        parsed = ipaddress.ip_interface(str(addresses[0].address))
        if parsed.version != 4 or parsed.network.prefixlen != 32:
            raise ValueError(f"{interface.name} must use one IPv4 /32 address")
        if parsed.ip not in LAB_PREFIX:
            raise ValueError(f"{interface.name} address must come from {LAB_PREFIX}")
        description = interface.description or "NETBOX_MANAGED_LAB18"
        if not DESCRIPTION_PATTERN.fullmatch(description):
            raise ValueError(f"{interface.name} description contains unsafe characters")
        loopback_id = int(match.group(1))
        address = str(parsed.ip)
        if loopback_id in seen_ids or address in seen_addresses:
            raise ValueError("Duplicate loopback ID or IPv4 address in NetBox intent")
        seen_ids.add(loopback_id)
        seen_addresses.add(address)
        desired.append(
            {
                "id": loopback_id,
                "name": interface.name,
                "address": address,
                "netmask": "255.255.255.255",
                "description": description,
                "netbox_interface_id": interface.id,
                "netbox_ip_id": addresses[0].id,
            }
        )
    return sorted(desired, key=lambda item: item["id"])


def write_plan(items, path="artifacts/loopback_plan.json"):
    Path(path).write_text(json.dumps({"loopbacks": items}, indent=2), encoding="utf-8")


def read_plan(path="artifacts/loopback_plan.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["loopbacks"]


def vault_device():
    client = hvac.Client(url=os.environ["VAULT_ADDR"], token=os.environ["VAULT_TOKEN"])
    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")
    secret = client.secrets.kv.v2.read_secret_version(
        mount_point="secret", path="ccnpauto/iosxe-netbox"
    )["data"]["data"]
    return {
        "device_type": "cisco_ios",
        "host": secret["host"],
        "port": int(secret.get("port", 22)),
        "username": secret["username"],
        "password": secret["password"],
    }


def connect_device():
    return ConnectHandler(**vault_device())
