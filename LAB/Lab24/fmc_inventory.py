#!/usr/bin/env python3
"""Authenticate to FMC and retrieve read-only managed-device inventory."""

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
    log = logging.getLogger("fmc")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(directory / f"fmc_{stamp}.log")
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


class FmcClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("FMC_BASE_URL", "").rstrip("/")
        self.username = os.getenv("FMC_USERNAME", "")
        self.password = os.getenv("FMC_PASSWORD", "")
        self.verify = os.getenv("FMC_VERIFY_TLS", "false").lower() == "true"
        if not all((self.base_url, self.username, self.password)):
            raise ValueError("Complete the FMC settings in .env")
        if not self.verify:
            disable_warnings(InsecureRequestWarning)
        self.session = requests.Session()
        self.session.verify = self.verify
        self.domain_uuid = ""

    def authenticate(self) -> None:
        response = self.session.post(
            f"{self.base_url}/api/fmc_platform/v1/auth/generatetoken",
            auth=(self.username, self.password),
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        token = response.headers.get("X-auth-access-token")
        self.domain_uuid = response.headers.get("DOMAIN_UUID", "")
        if not token or not self.domain_uuid:
            raise ValueError("FMC authentication response omitted its access token or DOMAIN_UUID")
        self.session.headers.update({"X-auth-access-token": token, "Accept": "application/json"})
        LOG.info("FMC authentication succeeded for domain %s", self.domain_uuid)

    def get(self, endpoint: str) -> dict[str, Any]:
        LOG.debug("GET %s", endpoint)
        response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
        response.raise_for_status()
        return response.json()


def main() -> None:
    try:
        client = FmcClient()
        client.authenticate()
        payload = client.get(f"/api/fmc_config/v1/domain/{client.domain_uuid}/devices/devicerecords?expanded=true")
        devices = payload.get("items", [])
        rows = [[d.get("name", "--"), d.get("hostName", "--"), d.get("model", "--"), d.get("healthStatus", "--"), d.get("sw_version", "--")] for d in devices]
        print(tabulate(rows, headers=["Name", "Hostname", "Model", "Health", "Version"], tablefmt="github"))
        artifact_dir = ROOT / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        output = artifact_dir / f"fmc_devices_{datetime.now():%Y%m%d_%H%M%S}.json"
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOG.info("Collected %d managed devices; saved %s", len(devices), output)
    except (RequestException, ValueError) as exc:
        LOG.error("FMC inventory failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
