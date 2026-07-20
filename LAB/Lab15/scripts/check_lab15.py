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

    for variable in ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD", "OLLAMA_URL", "OLLAMA_MODEL"]:
        if not os.getenv(variable):
            failures.append(f"Missing environment variable: {variable}")

    if failures:
        print("Lab 15 readiness check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Lab 15 readiness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
