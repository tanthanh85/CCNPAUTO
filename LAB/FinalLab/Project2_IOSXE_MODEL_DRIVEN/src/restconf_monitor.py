from __future__ import annotations

from typing import Any

import requests
from urllib3.exceptions import InsecureRequestWarning

from src.settings import load_settings


# TODO: Use Cisco YANG Suite to locate the correct RESTCONF data paths.
# Place only the RESTCONF data path beginning with "/".
CPU_URI = ""
MEMORY_URI = ""
INTERFACE_GIG1_URI = ""


class RestconfMonitorError(RuntimeError):
    pass


def restconf_get(path: str) -> dict[str, Any]:
    if not path:
        raise RestconfMonitorError("RESTCONF URI has not been completed")
    if not path.startswith("/"):
        raise RestconfMonitorError("RESTCONF URI must begin with '/'")

    settings = load_settings()
    if not settings.verify_tls:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    response = requests.get(
        f"{settings.restconf_base_url}{path}",
        auth=(settings.username, settings.password),
        headers={"Accept": "application/yang-data+json"},
        timeout=10,
        verify=settings.verify_tls,
    )
    response.raise_for_status()
    return response.json() if response.text else {}


def first_numeric_value(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        for child in value.values():
            found = first_numeric_value(child)
            if found is not None:
                return found
    if isinstance(value, list):
        for item in value:
            found = first_numeric_value(item)
            if found is not None:
                return found
    return None


def get_monitoring_snapshot() -> dict[str, Any]:
    cpu_data = restconf_get(CPU_URI)
    memory_data = restconf_get(MEMORY_URI)
    interface_data = restconf_get(INTERFACE_GIG1_URI)

    return {
        "cpu": {
            "uri": CPU_URI,
            "value": first_numeric_value(cpu_data),
            "raw": cpu_data,
        },
        "memory": {
            "uri": MEMORY_URI,
            "value": first_numeric_value(memory_data),
            "raw": memory_data,
        },
        "gigabit_ethernet_1": {
            "uri": INTERFACE_GIG1_URI,
            "value": first_numeric_value(interface_data),
            "raw": interface_data,
        },
    }

