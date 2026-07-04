#!/usr/bin/env python3

import json
from pathlib import Path

from src.payload import build_mdt_payload
from src.settings import Settings


try:
    settings = Settings()
    payload = build_mdt_payload(
        settings.receiver_ip,
        settings.receiver_port,
        settings.period_cs,
    )
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/mdt-subscriptions.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print("Created artifacts/mdt-subscriptions.json")
except (OSError, ValueError) as error:
    print(f"Preview failed: {error}")
