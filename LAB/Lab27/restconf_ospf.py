from __future__ import annotations

from collections import Counter
from typing import Any

from restconf_routes import IosXeRestconfClient


OSPF_OPERATIONAL_PATH = "/Cisco-IOS-XE-ospf-oper:ospf-oper-data"


def _local_name(key: str) -> str:
    return key.split(":")[-1]


def _collect_nodes(value: Any, names: set[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if _local_name(key) in names:
                if isinstance(child, dict):
                    matches.append(child)
                elif isinstance(child, list):
                    matches.extend(item for item in child if isinstance(item, dict))
            matches.extend(_collect_nodes(child, names))
    elif isinstance(value, list):
        for child in value:
            matches.extend(_collect_nodes(child, names))
    return matches


def _first_values(value: Any, names: set[str]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            local = _local_name(key)
            if local in names and not isinstance(child, (dict, list)):
                found.setdefault(local, child)
            elif isinstance(child, (dict, list)):
                for nested_key, nested_value in _first_values(child, names).items():
                    found.setdefault(nested_key, nested_value)
    elif isinstance(value, list):
        for child in value:
            for nested_key, nested_value in _first_values(child, names).items():
                found.setdefault(nested_key, nested_value)
    return found


def _compact(nodes: list[dict[str, Any]], fields: set[str]) -> list[dict[str, Any]]:
    return [_first_values(node, fields) for node in nodes[:20]]


def ospf_operational_status() -> dict[str, Any]:
    """Return bounded OSPF process, area, interface, and neighbor evidence."""
    payload = IosXeRestconfClient().get(OSPF_OPERATIONAL_PATH)
    processes = _collect_nodes(payload, {"ospf-instance", "ospfv2-instance"})
    areas = _collect_nodes(payload, {"ospf-area", "ospfv2-area"})
    interfaces = _collect_nodes(payload, {"ospf-interface", "ospfv2-interface"})
    neighbors = _collect_nodes(payload, {"ospf-neighbor", "ospfv2-neighbor"})

    process_rows = _compact(processes, {"process-id", "router-id", "vrf", "af"})
    area_rows = _compact(areas, {"area-id", "area-type", "auth-type"})
    interface_rows = _compact(
        interfaces,
        {"name", "interface", "area-id", "network-type", "state", "cost"},
    )
    neighbor_rows = _compact(
        neighbors,
        {"neighbor-id", "nbr-id", "address", "state", "nbr-state", "interface"},
    )
    state_counts = Counter(
        str(row.get("state") or row.get("nbr-state") or "unknown").lower()
        for row in neighbor_rows
    )
    return {
        "source_endpoint": OSPF_OPERATIONAL_PATH,
        "process_count": len(processes),
        "area_count": len(areas),
        "interface_count": len(interfaces),
        "neighbor_count": len(neighbors),
        "neighbor_state_counts": dict(sorted(state_counts.items())),
        "processes": process_rows,
        "areas": area_rows,
        "interfaces": interface_rows,
        "neighbors": neighbor_rows,
        "result_limit": 20,
    }
