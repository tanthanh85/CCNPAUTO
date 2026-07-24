from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_static_routes(path: str = "data/static_routes.yaml") -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    routes = data.get("static_routes", [])
    if not isinstance(routes, list):
        raise ValueError("static_routes must be a list")

    for route in routes:
        for key in ["prefix", "mask", "next_hop"]:
            if key not in route or not str(route[key]).strip():
                raise ValueError(f"Static route is missing {key}: {route}")

    return routes

