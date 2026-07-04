#!/usr/bin/env python3
"""Validate YAML loopback intent and print the rendered IOS XE commands."""

from pathlib import Path

from src.loopback_source import LoopbackManager


ROOT = Path(__file__).resolve().parents[1]
manager = LoopbackManager(
    ROOT / "data" / "loopbacks.yaml",
    ROOT / "templates" / "loopback.j2",
)

try:
    loopbacks = manager.load()
    commands = manager.render(loopbacks)
    print("\n".join(commands))
except ValueError as exc:
    raise SystemExit(f"Preview failed: {exc}") from exc

