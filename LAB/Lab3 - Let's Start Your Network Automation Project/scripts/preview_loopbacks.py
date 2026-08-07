#!/usr/bin/env python3
"""Validate YAML loopback intent and print the rendered IOS XE commands."""

import logging
from pathlib import Path

from src.logging_config import configure_logging
from src.loopback_source import LoopbackManager


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging("preview_loopbacks", project_root=ROOT)
    logger.info("Starting loopback intent preview")
    manager = LoopbackManager(
        ROOT / "data" / "loopbacks.yaml",
        ROOT / "templates" / "loopback.j2",
    )

    try:
        loopbacks = manager.load()
        logger.info("Validated %d loopback record(s)", len(loopbacks))
        commands = manager.render(loopbacks)
        logger.info("Rendered %d configuration command(s)", len(commands))
        logger.debug("Rendered commands=%s", commands)
        print("\n".join(commands))
    except ValueError as exc:
        logger.exception("Loopback preview failed")
        raise SystemExit(f"Preview failed: {exc}") from exc


if __name__ == "__main__":
    main()
