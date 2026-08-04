from __future__ import annotations

import logging
import os
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv
from urllib3.exceptions import InsecureRequestWarning


load_dotenv()
logger = logging.getLogger(__name__)


class RestconfError(RuntimeError):
    """Raised when IOS XE route information cannot be retrieved safely."""


class RestconfResourceNotFound(RestconfError):
    """Raised when one candidate YANG resource is not implemented."""


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
    values = {
        "IOSXE_HOST": os.getenv("IOSXE_HOST", "").strip(),
        "IOSXE_USERNAME": os.getenv("IOSXE_USERNAME", "").strip(),
        "IOSXE_PASSWORD": os.getenv("IOSXE_PASSWORD", "").strip(),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RestconfError(f"Missing required environment values: {missing}")
    return IosXeSettings(
        host=values["IOSXE_HOST"],
        port=int(os.getenv("IOSXE_RESTCONF_PORT", "443")),
        username=values["IOSXE_USERNAME"],
        password=values["IOSXE_PASSWORD"],
        verify_tls=os.getenv("IOSXE_VERIFY_TLS", "false").lower() == "true",
    )


class IosXeRestconfClient:
    def __init__(self) -> None:
        self.settings = load_settings()
        if not self.settings.verify_tls:
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        self.session = requests.Session()
        self.session.auth = (self.settings.username, self.settings.password)
        self.session.verify = self.settings.verify_tls
        self.session.headers.update({"Accept": "application/yang-data+json"})

    def get(self, path: str) -> dict[str, Any]:
        if not path.startswith("/"):
            raise ValueError("RESTCONF path must begin with '/'")
        url = f"{self.settings.base_url}{path}"
        started = time.perf_counter()
        logger.info("RESTCONF GET path=%s", path)
        try:
            response = self.session.get(url, timeout=20)
            logger.info(
                "RESTCONF response status=%d elapsed_seconds=%.3f bytes=%d",
                response.status_code,
                time.perf_counter() - started,
                len(response.content),
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.Timeout as exc:
            raise RestconfError(f"RESTCONF request timed out for {path}") from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            if status == 404:
                raise RestconfResourceNotFound(
                    f"RESTCONF resource is not implemented: {path}"
                ) from exc
            raise RestconfError(f"RESTCONF GET {path} returned HTTP {status}") from exc
        except (requests.exceptions.RequestException, ValueError) as exc:
            raise RestconfError(f"RESTCONF GET failed for {path}: {exc}") from exc


DEFAULT_ROUTE_ENDPOINTS = [
    # IOS XE releases used by the reservable sandbox commonly implement the
    # RFC 8022-era ietf-routing operational tree below.
    "/ietf-routing:routing-state/routing-instance=default/ribs/rib=ipv4-default/routes/route",
    "/ietf-routing:routing-state/routing-instance=default/ribs/rib=ipv4-default/routes",
    # Native FIB data is retained as a fallback for releases that do not expose
    # the IETF operational route tree.
    "/Cisco-IOS-XE-fib-oper:fib-oper-data",
]


def route_endpoints() -> list[str]:
    """Return an optional learner override followed by safe fallbacks."""
    override = os.getenv("IOSXE_ROUTE_ENDPOINT", "").strip()
    endpoints = ([override] if override else []) + DEFAULT_ROUTE_ENDPOINTS
    return list(dict.fromkeys(endpoints))


def _collect_by_key(value: Any, wanted: set[str]) -> list[Any]:
    matches: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in wanted and child not in (None, ""):
                matches.append(child)
            matches.extend(_collect_by_key(child, wanted))
    elif isinstance(value, list):
        for child in value:
            matches.extend(_collect_by_key(child, wanted))
    return matches


def _find_routes(value: Any) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if isinstance(value, dict):
        indicators = {
            "destination-prefix",
            "source-protocol",
            "route-pre",
            "prefix",
            "ip-addr",
            "next-hop",
        }
        if indicators.intersection(value):
            matches.append(value)
        for child in value.values():
            matches.extend(_find_routes(child))
    elif isinstance(value, list):
        for child in value:
            matches.extend(_find_routes(child))
    return matches


def _protocol(value: Any) -> str:
    text = str(value or "unknown")
    return text.split(":")[-1].replace("routing-protocol-", "")


def _normalize(route: dict[str, Any]) -> dict[str, Any]:
    prefix = (
        route.get("destination-prefix")
        or route.get("prefix")
        or route.get("route-pre")
        or route.get("ip-addr")
        or "unknown"
    )
    protocol = _protocol(
        route.get("source-protocol")
        or route.get("protocol")
        or route.get("route-type")
        or route.get("type")
    )
    next_hops = _collect_by_key(
        route,
        {"next-hop-address", "outgoing-interface", "special-next-hop", "nexthop-address", "nh-addr"},
    )
    metric = route.get("metric") or route.get("route-preference") or route.get("distance")
    return {
        "prefix": str(prefix),
        "protocol": protocol,
        "next_hops": [str(item) for item in next_hops] or ["directly-connected-or-unspecified"],
        "metric": metric if metric is not None else "unknown",
        "active": route.get("active", "unknown"),
    }


def get_routes() -> dict[str, Any]:
    client = IosXeRestconfClient()
    failures: list[str] = []
    endpoints = route_endpoints()
    for endpoint in endpoints:
        try:
            records = [_normalize(item) for item in _find_routes(client.get(endpoint))]
            if records:
                return {"source_endpoint": endpoint, "route_count": len(records), "routes": records}
            logger.info("Route endpoint returned no recognizable records endpoint=%s", endpoint)
        except RestconfResourceNotFound as exc:
            # Different IOS XE releases expose different revisions of the
            # routing model. A missing candidate is expected during discovery.
            logger.info("Route model unavailable endpoint=%s", endpoint)
            failures.append(str(exc))
        except RestconfError as exc:
            logger.warning("Route endpoint failed endpoint=%s error=%s", endpoint, exc)
            failures.append(str(exc))
    raise RestconfError(
        "No supported RESTCONF route endpoint returned route data. "
        f"Tried {endpoints}. Errors: {failures}"
    )


def route_summary() -> dict[str, Any]:
    data = get_routes()
    counts = Counter(route["protocol"] for route in data["routes"])
    return {
        "source_endpoint": data["source_endpoint"],
        "route_count": data["route_count"],
        "protocol_counts": dict(sorted(counts.items())),
    }


def routes_by_protocol(protocol: str) -> dict[str, Any]:
    requested = protocol.strip().lower()
    data = get_routes()
    routes = [route for route in data["routes"] if requested in route["protocol"].lower()]
    return {"requested_protocol": requested, "matched_count": len(routes), "routes": routes}


def route_detail(prefix: str) -> dict[str, Any]:
    requested = prefix.strip()
    data = get_routes()
    routes = [route for route in data["routes"] if route["prefix"] == requested]
    return {"requested_prefix": requested, "matched_count": len(routes), "routes": routes}
