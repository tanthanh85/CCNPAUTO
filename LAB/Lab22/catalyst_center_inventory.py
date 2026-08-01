#!/usr/bin/env python3
"""Retrieve read-only inventory from Catalyst Center 2.3.3.6."""

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


def logger() -> logging.Logger:
    directory = ROOT / "logs"
    directory.mkdir(exist_ok=True)
    log = logging.getLogger("catalyst_center")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(directory / f"catalyst_center_{stamp}.log")
    console_handler = logging.StreamHandler()
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.addHandler(console_handler)
    return log


LOG = logger()


class CatalystCenterClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("CATALYST_CENTER_BASE_URL", "").rstrip("/")
        self.username = os.getenv("CATALYST_CENTER_USERNAME", "")
        self.password = os.getenv("CATALYST_CENTER_PASSWORD", "")
        self.verify = os.getenv("CATALYST_CENTER_VERIFY_TLS", "false").lower() == "true"
        if not all((self.base_url, self.username, self.password)):
            raise ValueError("Complete the Catalyst Center settings in .env")
        if not self.verify:
            disable_warnings(InsecureRequestWarning)
        self.session = requests.Session()
        self.session.verify = self.verify

    def authenticate(self) -> None:
        response = self.session.post(
            f"{self.base_url}/dna/system/api/v1/auth/token",
            auth=(self.username, self.password),
            headers={"Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        token = response.json().get("Token")
        if not token:
            raise ValueError("Catalyst Center token response did not contain Token")
        self.session.headers.update({"X-Auth-Token": token, "Accept": "application/json"})
        LOG.info("Catalyst Center authentication succeeded")

    def get(self, endpoint: str) -> dict[str, Any]:
        LOG.debug("GET %s", endpoint)
        response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
        response.raise_for_status()
        return response.json()


def main() -> None:
    try:
        client = CatalystCenterClient()
        client.authenticate()
        devices_payload = client.get("/dna/intent/api/v1/network-device")
        sites_payload = client.get("/dna/intent/api/v1/site")
        devices = devices_payload.get("response", [])
        rows = [
            [d.get("hostname", "--"), d.get("family", "--"), d.get("managementIpAddress", "--"), d.get("softwareVersion", "--"), d.get("reachabilityStatus", "--")]
            for d in devices
        ]
        print(tabulate(rows, headers=["Hostname", "Family", "Management IP", "Version", "Reachability"], tablefmt="github"))
        artifact_dir = ROOT / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        output = artifact_dir / f"catalyst_center_{datetime.now():%Y%m%d_%H%M%S}.json"
        output.write_text(json.dumps({"devices": devices_payload, "sites": sites_payload}, indent=2), encoding="utf-8")
        LOG.info("Collected %d devices and saved %s", len(devices), output)
    except (RequestException, ValueError) as exc:
        LOG.error("Catalyst Center inventory failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
