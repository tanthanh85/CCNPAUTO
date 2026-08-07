#!/usr/bin/env python3
"""Confirm Vault retrieval without printing either credential."""

import logging
from pathlib import Path

from src.logging_config import configure_logging
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging("verify_vault", project_root=ROOT)
    logger.info("Starting Vault credential retrieval verification")
    try:
        settings = Settings()
        logger.info(
            "Vault credential verification passed username_length=%d "
            "password_length=%d",
            len(settings.username),
            len(settings.password),
        )
        print(
            f"PASS: Vault returned an IOS XE username with "
            f"{len(settings.username)} characters."
        )
        print(
            f"PASS: Vault returned a password with "
            f"{len(settings.password)} characters."
        )
    except (ValueError, RuntimeError) as exc:
        logger.exception("Vault credential verification failed")
        raise SystemExit(f"FAIL: {exc}") from exc


if __name__ == "__main__":
    main()
