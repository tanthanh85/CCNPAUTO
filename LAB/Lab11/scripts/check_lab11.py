from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logging_config import configure_logging


REQUIRED_MODULES = ["flask", "requests", "dotenv", "mcp"]
logger = logging.getLogger(__name__)


def main() -> int:
    load_dotenv()
    configure_logging("check_lab11")
    logger.info("Starting Lab 11 readiness validation")

    failures: list[str] = []

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ImportError:
            failures.append(f"Missing Python module: {module}")
            logger.exception("Required Python module is missing module=%s", module)

    for variable in ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD"]:
        if not os.getenv(variable):
            failures.append(f"Missing environment variable: {variable}")
            logger.error("Required environment variable is missing name=%s", variable)

    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    provider_variables = {
        "ollama": ["OLLAMA_URL", "OLLAMA_MODEL"],
        "vllm": ["VLLM_BASE_URL", "VLLM_MODEL", "VLLM_API_KEY"],
        "openai": ["OPENAI_API_KEY", "OPENAI_MODEL"],
        "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"],
    }
    if provider not in provider_variables:
        failures.append(
            "LLM_PROVIDER must be one of: ollama, vllm, openai, or anthropic"
        )
    else:
        for variable in provider_variables[provider]:
            if not os.getenv(variable):
                failures.append(
                    f"Missing environment variable for {provider}: {variable}"
                )

    if failures:
        logger.error("Lab 11 readiness failed failures=%s", failures)
        print("Lab 11 readiness check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    logger.info("Lab 11 readiness passed provider=%s", provider)
    print(f"Lab 11 readiness check passed for provider: {provider}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
