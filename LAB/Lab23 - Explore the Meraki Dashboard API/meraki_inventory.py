#!/usr/bin/env python3
"""Explore the Meraki Dashboard API with read-only requests."""

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


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def configure_logging() -> logging.Logger:
    directory = ROOT / "logs"
    directory.mkdir(exist_ok=True)
    log = logging.getLogger("meraki")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(directory / f"meraki_{stamp}.log")
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


class MerakiClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("MERAKI_BASE_URL", "https://api.meraki.com/api/v1").rstrip("/")
        api_key = os.getenv("MERAKI_API_KEY", "")
        if not api_key:
            raise ValueError("Set MERAKI_API_KEY in .env")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}", "Accept": "application/json"})

    def get_all(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        url: str | None = f"{self.base_url}{endpoint}"
        items: list[dict[str, Any]] = []
        while url:
            LOG.debug("GET %s", url)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise ValueError(f"Expected a JSON list from {endpoint}")
            items.extend(page)
            url = response.links.get("next", {}).get("url")
            params = None
        return items


def main() -> None:
    try:
        client = MerakiClient()
        organizations = client.get_all("/organizations")
        configured_org = os.getenv("MERAKI_ORG_ID", "").strip()
        organization_id = configured_org or (organizations[0]["id"] if organizations else "")
        if not organization_id:
            raise ValueError("The API key does not provide access to an organization")

        networks = client.get_all(f"/organizations/{organization_id}/networks", {"perPage": 1000})
        devices = client.get_all(f"/organizations/{organization_id}/devices", {"perPage": 1000})
        rows = [[d.get("name") or "--", d.get("model", "--"), d.get("serial", "--"), d.get("lanIp", "--"), d.get("networkId", "--")] for d in devices]
        print(tabulate(rows, headers=["Name", "Model", "Serial", "LAN IP", "Network ID"], tablefmt="github"))

        artifact_dir = ROOT / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        output = artifact_dir / f"meraki_{datetime.now():%Y%m%d_%H%M%S}.json"
        output.write_text(json.dumps({"organizations": organizations, "networks": networks, "devices": devices}, indent=2), encoding="utf-8")
        LOG.info("Collected %d networks and %d devices; saved %s", len(networks), len(devices), output)
    except (RequestException, ValueError, KeyError) as exc:
        LOG.error("Meraki inventory failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
