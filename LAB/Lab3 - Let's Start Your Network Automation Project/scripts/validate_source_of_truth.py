#!/usr/bin/env python3

import logging
from pathlib import Path

import yaml

from src.logging_config import configure_logging
from src.loopback_source import LoopbackManager


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging("validate_source_of_truth", project_root=ROOT)
    logger.info("Starting YAML source-of-truth validation")
    manager = LoopbackManager(
        ROOT / "data" / "loopbacks.yaml",
        ROOT / "templates" / "loopback.j2",
    )

    try:
        loopbacks = manager.load(require_entries=False)
        logger.info(
            "Source-of-truth validation passed records=%d path=%s",
            len(loopbacks),
            manager.yaml_path,
        )
        logger.debug("Validated loopback records=%s", loopbacks)
        print(f"PASS: data/loopbacks.yaml contains {len(loopbacks)} valid loopback(s).")
    except yaml.YAMLError as error:
        logger.exception("YAML syntax validation failed")
        print(f"FAIL: YAML syntax error: {error}")
        raise SystemExit(1)
    except ValueError as error:
        logger.exception("YAML semantic validation failed")
        print(f"FAIL: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
