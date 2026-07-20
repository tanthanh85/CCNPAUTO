from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv
from urllib3.exceptions import InsecureRequestWarning


load_dotenv()


class RestconfError(RuntimeError):
    """Raised when route information cannot be retrieved through RESTCONF."""


@dataclass(frozen=True)
class IosXeSettings:
    host: str
    port: int
    username: str
    password: str
    verify_tls: bool

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}/restconf/data"


def load_settings() -> IosXeSettings:
    host = os.getenv("IOSXE_HOST", "").strip()
    username = os.getenv("IOSXE_USERNAME", "").strip()
    password = os.getenv("IOSXE_PASSWORD", "").strip()
    port = int(os.getenv("IOSXE_RESTCONF_PORT", "443"))
    verify_tls = os.getenv("IOSXE_VERIFY_TLS", "true").lower() == "true"

    missing = [
        name
        for name, value in {
            "IOSXE_HOST": host,
            "IOSXE_USERNAME": username,
            "IOSXE_PASSWORD": password,
        }.items()
        if not value
    ]
    if missing:
        raise RestconfError(f"Missing required environment values: {missing}")

    return IosXeSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        verify_tls=verify_tls,
    )


class IosXeRestconfClient:
    def __init__(self, settings: IosXeSettings | None = None) -> None:
        self.settings = settings or load_settings()
        if not self.settings.verify_tls:
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        self.session = requests.Session()
        self.session.auth = (self.settings.username, self.settings.password)
        self.session.headers.update(
            {
                "Accept": "application/yang-data+json",
                "Content-Type": "application/yang-data+json",
            }
        )
        self.session.verify = self.settings.verify_tls

    def get(self, path: str) -> dict[str, Any]:
        if not path.startswith("/"):
            raise ValueError("RESTCONF path must begin with '/'")

        url = f"{self.settings.base_url}{path}"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise RestconfError(f"RESTCONF request timed out for {path}") from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response else "unknown"
            raise RestconfError(f"RESTCONF request failed for {path}: HTTP {status}") from exc
        except requests.exceptions.RequestException as exc:
            raise RestconfError(f"RESTCONF request failed for {path}") from exc

        return response.json() if response.text else {}


ROUTE_ENDPOINTS = [
    "/ietf-routing:routing/ribs/rib=ipv4-default/routes",
    "/ietf-routing:routing-state/routing-instance=default/ribs/rib=ipv4-default/routes",
    "/Cisco-IOS-XE-rib-oper:rib-ios-xe-oper-data/rib",
]


def find_route_dictionaries(value: Any) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []

    if isinstance(value, dict):
        route_like_keys = {
            "destination-prefix",
            "source-protocol",
            "next-hop",
            "route-preference",
            "active",
        }
        if route_like_keys.intersection(value.keys()):
            routes.append(value)

        for child in value.values():
            routes.extend(find_route_dictionaries(child))

    elif isinstance(value, list):
        for item in value:
            routes.extend(find_route_dictionaries(item))

    return routes


def collect_values_by_key(value: Any, wanted_keys: set[str]) -> list[Any]:
    matches: list[Any] = []

    if isinstance(value, dict):
        for key, child in value.items():
            if key in wanted_keys and child not in (None, ""):
                matches.append(child)
            matches.extend(collect_values_by_key(child, wanted_keys))

    elif isinstance(value, list):
        for item in value:
            matches.extend(collect_values_by_key(item, wanted_keys))

    return matches


def clean_protocol(protocol: Any) -> str:
    if protocol is None:
        return "unknown"
    text = str(protocol)
    return text.split(":")[-1].replace("routing-protocol-", "")


def normalize_route(route: dict[str, Any]) -> dict[str, Any]:
    prefix = (
        route.get("destination-prefix")
        or route.get("prefix")
        or route.get("route-pre")
        or "unknown"
    )
    protocol = clean_protocol(
        route.get("source-protocol")
        or route.get("protocol")
        or route.get("route-type")
        or route.get("type")
    )
    next_hops = collect_values_by_key(
        route,
        {
            "next-hop-address",
            "outgoing-interface",
            "special-next-hop",
            "nexthop-address",
            "nh-addr",
        },
    )

    metric = route.get("metric") or route.get("route-preference") or route.get("distance")

    return {
        "prefix": prefix,
        "protocol": protocol,
        "next_hops": [str(item) for item in next_hops] or ["directly-connected-or-unspecified"],
        "metric": metric if metric is not None else "unknown",
        "active": route.get("active", "unknown"),
        "raw": route,
    }


def get_routes() -> dict[str, Any]:
    client = IosXeRestconfClient()
    errors: list[str] = []

    for endpoint in ROUTE_ENDPOINTS:
        try:
            data = client.get(endpoint)
            raw_routes = find_route_dictionaries(data)
            routes = [normalize_route(item) for item in raw_routes]
            if routes:
                return {
                    "source_endpoint": endpoint,
                    "route_count": len(routes),
                    "routes": routes,
                }
        except RestconfError as exc:
            errors.append(str(exc))

    raise RestconfError(
        "No supported RESTCONF route endpoint returned route data. "
        "Use Cisco YANG Suite to confirm the routing operational model "
        f"for this IOS XE release. Tried: {ROUTE_ENDPOINTS}. Errors: {errors}"
    )


def route_summary() -> dict[str, Any]:
    data = get_routes()
    protocol_counts = Counter(route["protocol"] for route in data["routes"])
    return {
        "source_endpoint": data["source_endpoint"],
        "route_count": data["route_count"],
        "protocol_counts": dict(sorted(protocol_counts.items())),
    }


def routes_by_protocol(protocol: str) -> dict[str, Any]:
    protocol = protocol.lower().strip()
    data = get_routes()
    routes = [
        route
        for route in data["routes"]
        if protocol in route["protocol"].lower()
    ]
    return {
        "requested_protocol": protocol,
        "matched_count": len(routes),
        "routes": routes,
    }


def route_detail(prefix: str) -> dict[str, Any]:
    prefix = prefix.strip()
    data = get_routes()
    matches = [route for route in data["routes"] if route["prefix"] == prefix]
    return {
        "requested_prefix": prefix,
        "matched_count": len(matches),
        "routes": matches,
    }
