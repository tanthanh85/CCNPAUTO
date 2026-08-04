from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logging_config import configure_logging
from tool_agent import ToolCallingModel, discover_tools


def main() -> int:
    load_dotenv(ROOT / ".env")
    configure_logging("check_lab26")
    failures: list[str] = []

    for module in ["flask", "requests", "dotenv", "mcp", "jsonschema"]:
        try:
            importlib.import_module(module)
        except ImportError:
            failures.append(f"Missing Python module: {module}")

    for variable in ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD"]:
        if not os.getenv(variable):
            failures.append(f"Missing environment value: {variable}")

    try:
        model = ToolCallingModel()
        print(f"Provider: {model.info.name}; model: {model.info.model}")
    except Exception as exc:
        failures.append(str(exc))

    try:
        tools = asyncio.run(discover_tools())
        names = [tool["function"]["name"] for tool in tools]
        expected = {"get_route_summary", "get_routes_by_protocol", "get_route_detail", "get_all_routes"}
        missing = expected.difference(names)
        if missing:
            failures.append(f"MCP server did not advertise tools: {sorted(missing)}")
        print(f"Discovered MCP tools: {', '.join(names)}")
    except Exception as exc:
        failures.append(f"MCP discovery failed: {exc}")

    if failures:
        print("Lab 26 readiness check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Lab 26 readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
