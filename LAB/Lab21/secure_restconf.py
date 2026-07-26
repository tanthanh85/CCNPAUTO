#!/usr/bin/env python3
"""Call IOS XE RESTCONF while validating a locally issued TLS certificate."""

from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


RESOURCE = "/restconf/data/Cisco-IOS-XE-native:native/interface"


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("<"):
        raise ValueError(f"Set {name} in .env")
    return value


def build_session(username: str, password: str) -> requests.Session:
    session = requests.Session()
    session.auth = (username, password)
    session.headers.update({"Accept": "application/yang-data+json"})
    return session


def interface_names(payload: dict) -> list[str]:
    interface_root = payload.get("Cisco-IOS-XE-native:interface", {})
    names = []
    for family, records in interface_root.items():
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict) and "name" in record:
                names.append(f"{family}{record['name']}")
    return sorted(names)


def main() -> None:
    load_dotenv()
    base_url = required("IOSXE_BASE_URL").rstrip("/")
    ca_bundle = Path(required("CA_BUNDLE")).expanduser()
    if not ca_bundle.is_file():
        raise FileNotFoundError(f"CA bundle not found: {ca_bundle}")

    session = build_session(
        required("IOSXE_USERNAME"),
        required("IOSXE_PASSWORD"),
    )

    try:
        response = session.get(
            base_url + RESOURCE,
            timeout=float(os.getenv("REQUEST_TIMEOUT", "15")),
            verify=str(ca_bundle),
        )
        response.raise_for_status()
    except requests.exceptions.SSLError as exc:
        raise SystemExit(
            "TLS validation failed. Check the CA file, certificate SAN, "
            f"hostname, and certificate validity: {exc}"
        ) from exc
    except requests.RequestException as exc:
        raise SystemExit(f"RESTCONF request failed: {exc}") from exc

    names = interface_names(response.json())
    print(f"HTTPS validation succeeded for {base_url}")
    print(f"RESTCONF status: {response.status_code}")
    print(f"Configured interfaces ({len(names)}):")
    for name in names:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
