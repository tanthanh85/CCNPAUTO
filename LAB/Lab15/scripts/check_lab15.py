from __future__ import annotations

import importlib
import os
import sys

from dotenv import load_dotenv


REQUIRED_MODULES = ["flask", "requests", "dotenv", "mcp"]


def main() -> int:
    load_dotenv()

    failures: list[str] = []

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ImportError:
            failures.append(f"Missing Python module: {module}")

    for variable in ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD"]:
        if not os.getenv(variable):
            failures.append(f"Missing environment variable: {variable}")

    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    provider_variables = {
        "ollama": ["OLLAMA_URL", "OLLAMA_MODEL"],
        "openai": ["OPENAI_API_KEY", "OPENAI_MODEL"],
        "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"],
    }
    if provider not in provider_variables:
        failures.append(
            "LLM_PROVIDER must be one of: ollama, openai, or anthropic"
        )
    else:
        for variable in provider_variables[provider]:
            if not os.getenv(variable):
                failures.append(
                    f"Missing environment variable for {provider}: {variable}"
                )

    if failures:
        print("Lab 15 readiness check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Lab 15 readiness check passed for provider: {provider}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
