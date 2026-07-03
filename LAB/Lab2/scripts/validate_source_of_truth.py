#!/usr/bin/env python3
"""Validate loopback YAML syntax, schema, and cross-record constraints."""

from pathlib import Path

from src.loopback_source import load_loopbacks


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = PROJECT_ROOT / "data" / "loopbacks.yaml"
    loopbacks = load_loopbacks(path, require_entries=False)
    print(
        f"PASS: {path.relative_to(PROJECT_ROOT)} is valid and contains "
        f"{len(loopbacks)} managed loopback interface(s)."
    )


if __name__ == "__main__":
    main()
