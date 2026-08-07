#!/usr/bin/env python3
"""Create and verify a three-tier ACI application policy on a reserved APIC."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
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

VRF = "ThreeTier-VRF"
APPLICATION_PROFILE = "ThreeTier-App"
BDS = {
    "Web-BD": "10.10.10.1/24",
    "App-BD": "10.10.20.1/24",
    "Database-BD": "10.10.30.1/24",
}


def configure_logging() -> logging.Logger:
    directory = ROOT / "logs"
    directory.mkdir(exist_ok=True)
    log = logging.getLogger("aci_three_tier")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(directory / f"aci_three_tier_{stamp}.log")
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


class AciLabError(RuntimeError):
    """Raised when the lab settings or APIC response is invalid."""


class ApicClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("APIC_BASE_URL", "").rstrip("/")
        self.username = os.getenv("APIC_USERNAME", "")
        self.password = os.getenv("APIC_PASSWORD", "")
        self.verify = os.getenv("APIC_VERIFY_TLS", "false").lower() == "true"
        self.tenant = os.getenv("ACI_TENANT", "")
        self.allow_changes = os.getenv("ACI_ALLOW_CHANGES", "false").lower() == "true"

        if not all((self.base_url, self.username, self.password, self.tenant)):
            raise AciLabError("Complete the APIC and ACI_TENANT settings in .env")
        if "REPLACE" in self.tenant.upper():
            raise AciLabError("Replace REPLACE_INITIALS in ACI_TENANT with your initials")
        if not self.tenant.startswith("CCNPAUTO-ThreeTier-"):
            raise AciLabError("ACI_TENANT must begin with CCNPAUTO-ThreeTier-")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", self.tenant):
            raise AciLabError("ACI_TENANT may contain letters, numbers, dot, underscore, colon, and hyphen")

        if not self.verify:
            disable_warnings(InsecureRequestWarning)
        self.session = requests.Session()
        self.session.verify = self.verify
        self.session.headers.update({"Accept": "application/json"})

    @property
    def tenant_path(self) -> str:
        return f"/api/node/mo/uni/tn-{self.tenant}.json"

    def authenticate(self) -> None:
        payload = {
            "aaaUser": {
                "attributes": {"name": self.username, "pwd": self.password}
            }
        }
        response = self.session.post(
            f"{self.base_url}/api/aaaLogin.json", json=payload, timeout=30
        )
        response.raise_for_status()
        if not response.json().get("imdata"):
            raise AciLabError("APIC login response did not contain aaaLogin data")
        LOG.info("Authenticated to APIC; session credentials are not logged")

    def require_changes_enabled(self) -> None:
        if not self.allow_changes:
            raise AciLabError(
                "Configuration is disabled. Use a reservable ACI Simulator 6.0 "
                "and set ACI_ALLOW_CHANGES=true in .env."
            )

    def apply(self, payload: dict[str, Any]) -> None:
        self.require_changes_enabled()
        LOG.info("Applying three-tier policy to tenant %s", self.tenant)
        response = self.session.post(
            f"{self.base_url}{self.tenant_path}", json=payload, timeout=60
        )
        if response.status_code not in (200, 201):
            raise AciLabError(
                f"APIC apply returned HTTP {response.status_code}: {response.text[:500]}"
            )

    def get_tenant(self) -> dict[str, Any] | None:
        response = self.session.get(
            f"{self.base_url}{self.tenant_path}",
            params={"rsp-subtree": "full"},
            timeout=60,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        objects = response.json().get("imdata", [])
        return objects[0] if objects else None

    def delete_tenant(self) -> None:
        self.require_changes_enabled()
        LOG.warning("Deleting learner-owned tenant %s", self.tenant)
        response = self.session.delete(
            f"{self.base_url}{self.tenant_path}", timeout=60
        )
        if response.status_code not in (200, 204):
            raise AciLabError(
                f"APIC delete returned HTTP {response.status_code}: {response.text[:500]}"
            )


def relationship(class_name: str, attributes: dict[str, str]) -> dict[str, Any]:
    return {class_name: {"attributes": attributes}}


def bridge_domain(name: str, gateway: str) -> dict[str, Any]:
    return {
        "fvBD": {
            "attributes": {
                "name": name,
                "arpFlood": "yes",
                "unicastRoute": "yes",
            },
            "children": [
                relationship("fvRsCtx", {"tnFvCtxName": VRF}),
                relationship(
                    "fvSubnet", {"ip": gateway, "scope": "private"}
                ),
            ],
        }
    }


def contract_filter(name: str, entry_name: str, port: str) -> dict[str, Any]:
    return {
        "vzFilter": {
            "attributes": {"name": name},
            "children": [
                relationship(
                    "vzEntry",
                    {
                        "name": entry_name,
                        "etherT": "ip",
                        "prot": "tcp",
                        "dFromPort": port,
                        "dToPort": port,
                    },
                )
            ],
        }
    }


def contract(name: str, filter_name: str) -> dict[str, Any]:
    return {
        "vzBrCP": {
            "attributes": {"name": name, "scope": "context"},
            "children": [
                {
                    "vzSubj": {
                        "attributes": {"name": f"{name}-Subject"},
                        "children": [
                            relationship(
                                "vzRsSubjFiltAtt",
                                {"tnVzFilterName": filter_name},
                            )
                        ],
                    }
                }
            ],
        }
    }


def epg(
    name: str,
    bd_name: str,
    provided: list[str] | None = None,
    consumed: list[str] | None = None,
) -> dict[str, Any]:
    children = [relationship("fvRsBd", {"tnFvBDName": bd_name})]
    children.extend(
        relationship("fvRsProv", {"tnVzBrCPName": item})
        for item in (provided or [])
    )
    children.extend(
        relationship("fvRsCons", {"tnVzBrCPName": item})
        for item in (consumed or [])
    )
    return {"fvAEPg": {"attributes": {"name": name}, "children": children}}


def build_three_tier_payload(tenant: str) -> dict[str, Any]:
    """Return one declarative tenant subtree for the three-tier application."""
    return {
        "fvTenant": {
            "attributes": {
                "name": tenant,
                "descr": "CCNPAUTO three-tier Web, App, and Database policy",
            },
            "children": [
                {"fvCtx": {"attributes": {"name": VRF, "pcEnfPref": "enforced"}}},
                *(bridge_domain(name, gateway) for name, gateway in BDS.items()),
                contract_filter("Web-to-App-Filter", "tcp-8443", "8443"),
                contract_filter("App-to-Database-Filter", "tcp-5432", "5432"),
                contract("Web-to-App", "Web-to-App-Filter"),
                contract("App-to-Database", "App-to-Database-Filter"),
                {
                    "fvAp": {
                        "attributes": {"name": APPLICATION_PROFILE},
                        "children": [
                            epg("Web-EPG", "Web-BD", consumed=["Web-to-App"]),
                            epg(
                                "App-EPG",
                                "App-BD",
                                provided=["Web-to-App"],
                                consumed=["App-to-Database"],
                            ),
                            epg(
                                "Database-EPG",
                                "Database-BD",
                                provided=["App-to-Database"],
                            ),
                        ],
                    }
                },
            ],
        }
    }


def collect_objects(node: Any, result: dict[str, list[str]]) -> None:
    if isinstance(node, list):
        for item in node:
            collect_objects(item, result)
        return
    if not isinstance(node, dict):
        return
    for class_name, body in node.items():
        if not isinstance(body, dict):
            continue
        attributes = body.get("attributes", {})
        name = attributes.get("name") or attributes.get("ip")
        if name:
            result.setdefault(class_name, []).append(str(name))
        collect_objects(body.get("children", []), result)


def show_summary(tenant_object: dict[str, Any] | None) -> None:
    if tenant_object is None:
        print("The learner tenant does not exist on APIC.")
        return
    objects: dict[str, list[str]] = {}
    collect_objects(tenant_object, objects)
    rows = [
        ["Tenant", ", ".join(objects.get("fvTenant", []))],
        ["VRF", ", ".join(objects.get("fvCtx", []))],
        ["Bridge domains", ", ".join(objects.get("fvBD", []))],
        ["Subnets", ", ".join(objects.get("fvSubnet", []))],
        ["Application profile", ", ".join(objects.get("fvAp", []))],
        ["EPGs", ", ".join(objects.get("fvAEPg", []))],
        ["Contracts", ", ".join(objects.get("vzBrCP", []))],
        ["Filters", ", ".join(objects.get("vzFilter", []))],
    ]
    print(tabulate(rows, headers=["Resource", "Observed names"], tablefmt="github"))


def save_artifact(tenant: str, data: dict[str, Any] | None) -> Path:
    directory = ROOT / "artifacts"
    directory.mkdir(exist_ok=True)
    output = directory / f"aci_{tenant}_{datetime.now():%Y%m%d_%H%M%S}.json"
    output.write_text(json.dumps(data or {}, indent=2), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="create or update the three-tier tenant")
    action.add_argument("--delete", action="store_true", help="delete only the learner-owned lab tenant")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        client = ApicClient()
        client.authenticate()
        if args.apply:
            client.apply(build_three_tier_payload(client.tenant))
            LOG.info("Three-tier policy accepted by APIC")
        elif args.delete:
            client.delete_tenant()
            LOG.info("Tenant deletion request accepted")

        observed = client.get_tenant()
        show_summary(observed)
        artifact = save_artifact(client.tenant, observed)
        LOG.info("Saved observed tenant state to %s", artifact)
    except (RequestException, AciLabError, ValueError) as exc:
        LOG.error("ACI lab failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
