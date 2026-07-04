#!/usr/bin/env python3

import json
from pathlib import Path

from src.payloads import build_netconf_interfaces, build_ospf_router_payload
from src.settings import Settings


try:
    settings = Settings()
    loopbacks = settings.loopbacks()
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)

    xml_payload = build_netconf_interfaces(loopbacks)
    json_payload = build_ospf_router_payload(loopbacks, settings.ospf_process_id)

    (artifacts / "netconf-loopbacks.xml").write_text(xml_payload, encoding="utf-8")
    (artifacts / "restconf-ospf.json").write_text(
        json.dumps(json_payload, indent=2), encoding="utf-8"
    )
    print("Created artifacts/netconf-loopbacks.xml")
    print("Created artifacts/restconf-ospf.json")
except (OSError, ValueError) as error:
    print(f"Payload preview failed: {error}")
