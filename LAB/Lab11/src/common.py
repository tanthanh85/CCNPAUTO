"""Vault, VLAN validation, device access, and audit helpers."""

import logging
import os
import re
import time
from pathlib import Path

import yaml


def configure_logging(filename):
    Path("artifacts").mkdir(exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S"
    )
    formatter.converter = time.gmtime
    file_handler = logging.FileHandler(f"artifacts/{filename}")
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler],
    )


def load_vlans(path="data/vlans.yaml"):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if set(data) != {"vlans"} or not isinstance(data["vlans"], list):
        raise ValueError("The file must contain one 'vlans' list")
    seen = set()
    validated = []
    for position, vlan in enumerate(data["vlans"], 1):
        if not isinstance(vlan, dict) or set(vlan) != {"id", "name"}:
            raise ValueError(f"VLAN item {position} must contain id and name")
        if type(vlan["id"]) is not int or not 1 <= vlan["id"] <= 4094:
            raise ValueError(f"VLAN item {position} has an invalid ID")
        if vlan["id"] in seen:
            raise ValueError(f"Duplicate VLAN ID {vlan['id']}")
        if not re.fullmatch(r"[A-Z0-9_-]{1,32}", str(vlan["name"])):
            raise ValueError(f"VLAN {vlan['id']} has an invalid name")
        seen.add(vlan["id"])
        validated.append(vlan)
    if not validated:
        raise ValueError("At least one VLAN is required")
    return validated


def vault_credentials():
    import hvac

    address = os.environ.get("VAULT_ADDR")
    token = os.environ.get("VAULT_TOKEN")
    if not address or not token:
        raise ValueError("VAULT_ADDR and VAULT_TOKEN must be protected CI variables")
    client = hvac.Client(url=address, token=token)
    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")
    response = client.secrets.kv.v2.read_secret_version(
        mount_point="secret", path="ccnpauto/catalyst9000v"
    )
    secret = response["data"]["data"]
    return {
        "device_type": "cisco_ios",
        "host": secret["host"],
        "port": int(secret.get("port", 22)),
        "username": secret["username"],
        "password": secret["password"],
    }


def connect():
    from netmiko import ConnectHandler

    return ConnectHandler(**vault_credentials())
