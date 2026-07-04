#!/usr/bin/env python3
"""Confirm Vault retrieval without printing either credential."""

from src.settings import Settings


try:
    settings = Settings()
    print(f"PASS: Vault returned an IOS XE username with {len(settings.username)} characters.")
    print(f"PASS: Vault returned a password with {len(settings.password)} characters.")
except (ValueError, RuntimeError) as exc:
    raise SystemExit(f"FAIL: {exc}") from exc

