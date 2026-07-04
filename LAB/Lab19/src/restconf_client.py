"""Small, read-only RESTCONF client for IOS XE routing information."""

from __future__ import annotations

import ipaddress
import os
from collections import Counter
from typing import Any

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()


class RestconfError(RuntimeError):
    """Represent a controlled RESTCONF or response-format failure."""


class IOSXERoutingClient:
    """Read and normalize the IOS XE operational routing table."""

    def __init__(self) -> None:
        self.host = os.getenv("IOSXE_HOST", "").strip()
        self.port = int(os.getenv("IOSXE_PORT", "443"))
        self.username = os.getenv("IOSXE_USERNAME", "").strip()
        self.password = os.getenv("IOSXE_PASSWORD", "")
        self.verify_tls = os.getenv("IOSXE_VERIFY_TLS", "false").lower() == "true"
        self.timeout = int(os.getenv("RESTCONF_TIMEOUT", "20"))
        self.rib_path = os.getenv(
            "IOSXE_RIB_PATH", "/restconf/data/Cisco-IOS-XE-rib-oper:rib"
        )
        if not all((self.host, self.username, self.password)):
            raise RestconfError("IOSXE_HOST, IOSXE_USERNAME, and IOSXE_PASSWORD are required")
        if not self.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get(self, path: str) -> dict[str, Any]:
        url = f"https://{self.host}:{self.port}{path}"
        headers = {"Accept": "application/yang-data+json"}
        try:
            response = requests.get(
                url,
                headers=headers,
                auth=(self.username, self.password),
                timeout=self.timeout,
                verify=self.verify_tls,
            )
        except requests.Timeout as exc:
            raise RestconfError(f"RESTCONF timed out after {self.timeout} seconds") from exc
        except requests.RequestException as exc:
            raise RestconfError(f"RESTCONF connection failed: {exc}") from exc

        if response.status_code != 200:
            detail = response.text.replace("\n", " ")[:300]
            raise RestconfError(
                f"RESTCONF returned HTTP {response.status_code} for {path}: {detail}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise RestconfError("IOS XE returned a non-JSON RESTCONF response") from exc

    @staticmethod
    def _local_name(name: str) -> str:
        return name.split(":")[-1]

    @classmethod
    def _value(cls, item: dict[str, Any], *names: str) -> Any:
        wanted = set(names)
        for key, value in item.items():
            if cls._local_name(key) in wanted:
                return value
        return None

    @classmethod
    def normalize_routes(cls, payload: Any) -> list[dict[str, Any]]:
        """Find route records in namespaced IOS XE JSON and normalize common fields."""
        routes: list[dict[str, Any]] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                prefix = cls._value(node, "prefix", "route-prefix", "destination-prefix")
                if isinstance(prefix, str) and "/" in prefix:
                    protocol = cls._value(
                        node, "route-source", "source-protocol", "protocol", "route-type"
                    )
                    next_hop = cls._value(
                        node, "next-hop-address", "next-hop", "gateway-address"
                    )
                    interface = cls._value(
                        node, "outgoing-interface", "interface-name", "outgoing-interface-name"
                    )
                    if isinstance(next_hop, dict):
                        interface = interface or cls._value(
                            next_hop, "outgoing-interface", "interface-name"
                        )
                        next_hop = cls._value(
                            next_hop, "next-hop-address", "address", "gateway-address"
                        )
                    routes.append(
                        {
                            "prefix": prefix,
                            "protocol": str(protocol or "unknown"),
                            "next_hop": str(next_hop or "directly connected"),
                            "interface": str(interface or "unknown"),
                            "distance": cls._value(
                                node, "distance", "administrative-distance", "route-preference"
                            ),
                            "metric": cls._value(node, "metric", "route-metric"),
                        }
                    )
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)
        unique = {tuple(sorted(route.items())): route for route in routes}
        return sorted(unique.values(), key=lambda route: route["prefix"])

    def routes(self) -> list[dict[str, Any]]:
        routes = self.normalize_routes(self._get(self.rib_path))
        if not routes:
            raise RestconfError(
                "No route records were recognized. Use YANG Suite to inspect the RIB payload "
                "and adjust IOSXE_RIB_PATH or the normalizer for this IOS XE release."
            )
        return routes

    def filtered_routes(
        self, protocol: str = "", prefix: str = "", limit: int = 50
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        protocol = protocol.strip().lower()
        prefix = prefix.strip()
        result = self.routes()
        if protocol:
            result = [r for r in result if protocol in r["protocol"].lower()]
        if prefix:
            result = [r for r in result if prefix in r["prefix"]]
        return result[:limit]

    def summary(self) -> dict[str, Any]:
        routes = self.routes()
        protocols = Counter(route["protocol"] for route in routes)
        defaults = [route for route in routes if route["prefix"] in {"0.0.0.0/0", "::/0"}]
        return {
            "total_routes": len(routes),
            "routes_by_protocol": dict(sorted(protocols.items())),
            "default_routes": defaults,
        }

    def longest_match(self, destination: str) -> dict[str, Any] | None:
        try:
            address = ipaddress.ip_address(destination.strip())
        except ValueError as exc:
            raise RestconfError(f"'{destination}' is not a valid IPv4 or IPv6 address") from exc
        matches = []
        for route in self.routes():
            try:
                network = ipaddress.ip_network(route["prefix"], strict=False)
            except ValueError:
                continue
            if address.version == network.version and address in network:
                matches.append((network.prefixlen, route))
        return max(matches, key=lambda item: item[0])[1] if matches else None

