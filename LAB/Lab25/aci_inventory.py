#!/usr/bin/env python3
"""Explore ACI managed objects through the APIC REST API."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from tabulate import tabulate
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def configure_logging() -> logging.Logger:
    directory = ROOT / "logs"
    directory.mkdir(exist_ok=True)
    log = logging.getLogger("aci")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(directory / f"aci_{stamp}.log")
    console_handler = logging.StreamHandler()
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.addHandler(console_handler)
    return log


LOG = configure_logging()


class ApicClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("APIC_BASE_URL", "").rstrip("/")
        self.username = os.getenv("APIC_USERNAME", "")
        self.password = os.getenv("APIC_PASSWORD", "")
        self.verify = os.getenv("APIC_VERIFY_TLS", "false").lower() == "true"
        if not all((self.base_url, self.username, self.password)):
            raise ValueError("Complete the APIC settings in .env")
        if not self.verify:
            disable_warnings(InsecureRequestWarning)
        self.session = requests.Session()
        self.session.verify = self.verify

    def authenticate(self) -> None:
        payload = {"aaaUser": {"attributes": {"name": self.username, "pwd": self.password}}}
        response = self.session.post(f"{self.base_url}/api/aaaLogin.json", json=payload, timeout=30)
        response.raise_for_status()
        objects = response.json().get("imdata", [])
        if not objects:
            raise ValueError("APIC login response did not contain an authentication object")
        LOG.info("APIC authentication succeeded")

    def class_query(self, class_name: str) -> list[dict[str, Any]]:
        endpoint = f"/api/node/class/{class_name}.json"
        LOG.debug("GET %s", endpoint)
        response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
        response.raise_for_status()
        return response.json().get("imdata", [])


def attributes(item: dict[str, Any]) -> dict[str, Any]:
    if not item:
        return {}
    return next(iter(item.values())).get("attributes", {})


def main() -> None:
    try:
        client = ApicClient()
        client.authenticate()
        controllers = client.class_query("topSystem")
        tenants = client.class_query("fvTenant")
        vrfs = client.class_query("fvCtx")
        bridge_domains = client.class_query("fvBD")
        rows = [[a.get("name", "--"), a.get("dn", "--"), a.get("descr", "")] for a in map(attributes, tenants)]
        print(tabulate(rows, headers=["Tenant", "Distinguished name", "Description"], tablefmt="github"))
        artifact_dir = ROOT / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        output = artifact_dir / f"aci_inventory_{datetime.now():%Y%m%d_%H%M%S}.json"
        output.write_text(json.dumps({"controllers": controllers, "tenants": tenants, "vrfs": vrfs, "bridge_domains": bridge_domains}, indent=2), encoding="utf-8")
        LOG.info("Collected %d tenants, %d VRFs, and %d bridge domains; saved %s", len(tenants), len(vrfs), len(bridge_domains), output)
    except (RequestException, ValueError) as exc:
        LOG.error("ACI inventory failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
