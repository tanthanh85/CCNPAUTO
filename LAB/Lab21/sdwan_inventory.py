#!/usr/bin/env python3
"""Collect a read-only Cisco SD-WAN 20.10 device inventory."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from requests import Session
from requests.exceptions import RequestException
from tabulate import tabulate
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def configure_logging() -> logging.Logger:
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = logging.getLogger("sdwan_inventory")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    file_handler = logging.FileHandler(log_dir / f"sdwan_{timestamp}.log")
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


LOG = configure_logging()


class SdwanApiError(RuntimeError):
    """Raised when SD-WAN Manager rejects or cannot complete a request."""


class SdwanClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("SDWAN_BASE_URL", "").rstrip("/")
        self.username = os.getenv("SDWAN_USERNAME", "")
        self.password = os.getenv("SDWAN_PASSWORD", "")
        self.verify_tls = os.getenv("SDWAN_VERIFY_TLS", "false").lower() == "true"
        if not all((self.base_url, self.username, self.password)):
            raise SdwanApiError("Complete SDWAN_BASE_URL, SDWAN_USERNAME, and SDWAN_PASSWORD in .env")
        if not self.verify_tls:
            disable_warnings(InsecureRequestWarning)
        self.session = Session()
        self.session.verify = self.verify_tls

    def authenticate(self) -> None:
        LOG.info("Authenticating to Cisco SD-WAN Manager 20.10")
        response = self.session.post(
            f"{self.base_url}/j_security_check",
            data={"j_username": self.username, "j_password": self.password},
            timeout=20,
        )
        response.raise_for_status()
        if "<html" in response.text.lower() or "JSESSIONID" not in self.session.cookies:
            raise SdwanApiError("Authentication failed: verify the reservation credentials")

        token_response = self.session.get(
            f"{self.base_url}/dataservice/client/token", timeout=20
        )
        token_response.raise_for_status()
        token = token_response.text.strip()
        if token:
            self.session.headers.update({"X-XSRF-TOKEN": token})
        self.session.headers.update({"Accept": "application/json"})
        LOG.info("SD-WAN session established; credentials and tokens are not logged")

    def get(self, endpoint: str) -> dict[str, Any]:
        LOG.debug("GET %s", endpoint)
        response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
        if response.status_code != 200:
            raise SdwanApiError(f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]}")
        return response.json()


def main() -> None:
    try:
        client = SdwanClient()
        client.authenticate()
        payload = client.get("/dataservice/device")
        devices = payload.get("data", [])

        rows = [
            [
                device.get("host-name", "--"),
                device.get("device-type", "--"),
                device.get("device-model", "--"),
                device.get("system-ip", "--"),
                device.get("reachability", "--"),
                device.get("version", "--"),
            ]
            for device in devices
        ]
        print(tabulate(rows, headers=["Host", "Type", "Model", "System IP", "Reachability", "Version"], tablefmt="github"))

        artifact_dir = ROOT / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        output = artifact_dir / f"sdwan_devices_{datetime.now():%Y%m%d_%H%M%S}.json"
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOG.info("Collected %d devices; saved %s", len(devices), output)
    except (RequestException, SdwanApiError, ValueError) as exc:
        LOG.error("SD-WAN inventory failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
