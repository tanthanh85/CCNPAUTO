#!/usr/bin/env python3

from pathlib import Path

import yaml

from src.loopback_source import LoopbackManager


ROOT = Path(__file__).resolve().parents[1]
manager = LoopbackManager(
    ROOT / "data" / "loopbacks.yaml",
    ROOT / "templates" / "loopback.j2",
)

try:
    loopbacks = manager.load(require_entries=False)
    print(f"PASS: data/loopbacks.yaml contains {len(loopbacks)} valid loopback(s).")
except yaml.YAMLError as error:
    print(f"FAIL: YAML syntax error: {error}")
    raise SystemExit(1)
except ValueError as error:
    print(f"FAIL: {error}")
    raise SystemExit(1)
