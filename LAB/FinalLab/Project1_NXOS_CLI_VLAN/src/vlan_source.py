from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_vlan_intent(path: str = "data/vlans.yaml") -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    vlans = data.get("vlans", [])
    if not isinstance(vlans, list):
        raise ValueError("vlans must be a list")

    for vlan in vlans:
        if "id" not in vlan or "name" not in vlan:
            raise ValueError(f"Invalid VLAN record: {vlan}")
        int(vlan["id"])
        if not str(vlan["name"]).strip():
            raise ValueError(f"VLAN {vlan['id']} has an empty name")

    return vlans

