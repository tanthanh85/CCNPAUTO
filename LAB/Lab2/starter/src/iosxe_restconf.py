"""RESTCONF client and response normalizer for IOS XE interface data."""

from __future__ import annotations

from typing import Any

import requests
import urllib3

from src.settings import Settings


class IOSXERESTCONFClient:
    INTERFACES_PATH = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
    IETF_INTERFACES_PATH = "/restconf/data/ietf-interfaces:interfaces-state"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = f"https://{settings.host}:{settings.https_port}"
        self.session = requests.Session()
        self.session.auth = (settings.username, settings.password)
        self.session.headers.update(
            {
                "Accept": "application/yang-data+json",
                "Content-Type": "application/yang-data+json",
            }
        )
        self.session.verify = settings.verify_tls
        if not settings.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get(self, path: str) -> dict[str, Any]:
        response = self.session.get(f"{self.base_url}{path}", timeout=(10, 45))
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:500]
            raise RuntimeError(
                f"RESTCONF GET {path} failed with HTTP {response.status_code}: {detail}"
            ) from exc
        return response.json()

    def get_interfaces_payload(self) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{self.INTERFACES_PATH}", timeout=(10, 45)
        )
        if response.status_code == 404:
            return self.get(self.IETF_INTERFACES_PATH)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"RESTCONF GET {self.INTERFACES_PATH} failed with HTTP "
                f"{response.status_code}: {response.text[:500]}"
            ) from exc
        return response.json()


def _status(value: Any, prefixes: tuple[str, ...]) -> str:
    text = str(value or "unknown")
    for prefix in prefixes:
        text = text.removeprefix(prefix)
    text = text.replace("-state", "").replace("-oper", "")
    return "up" if text == "ready" else text


def normalize_interfaces(payload: dict[str, Any]) -> list[dict[str, Any]]:
    root = payload.get("Cisco-IOS-XE-interfaces-oper:interfaces")
    if root is None:
        root = payload.get("ietf-interfaces:interfaces-state", {})
    entries = root.get("interface", [])
    if not isinstance(entries, list):
        raise ValueError("Unexpected RESTCONF response: interface is not a list")

    records: list[dict[str, Any]] = []
    for entry in entries:
        ipv4 = entry.get("ipv4", entry.get("ietf-ip:ipv4", "unassigned"))
        if isinstance(ipv4, dict):
            addresses = ipv4.get("address", [])
            ipv4 = addresses[0].get("ip", "unassigned") if addresses else "unassigned"

        records.append(
            {
                "interface": entry.get("name", "-"),
                "ip_address": ipv4 or "unassigned",
                "status": _status(entry.get("admin-status"), ("if-state-",)),
                "protocol": _status(
                    entry.get("oper-status"),
                    ("if-oper-state-", "if-oper-"),
                ),
            }
        )
    return records
