from __future__ import annotations

from typing import Any

from mcp_server import (
    route_tool_all,
    route_tool_by_protocol,
    route_tool_detail,
    route_tool_summary,
)
from restconf_routes import RestconfError


class McpToolError(RuntimeError):
    """Raised when a route-information MCP tool cannot return data."""


def call_route_tool(tool_name: str, **kwargs: Any) -> dict[str, Any]:
    """Call the local MCP route tool abstraction used by the Flask assistant.

    The Flask web application must not retrieve route data from RESTCONF directly.
    It asks this MCP client abstraction for route context. The callable tools live
    in mcp_server.py, and mcp_server.py is the layer that retrieves IOS XE route
    information through RESTCONF.
    """

    tools = {
        "get_route_summary": route_tool_summary,
        "get_routes_by_protocol": route_tool_by_protocol,
        "get_route_detail": route_tool_detail,
        "get_all_routes": route_tool_all,
    }

    if tool_name not in tools:
        raise ValueError(f"Unsupported MCP route tool: {tool_name}")

    try:
        return tools[tool_name](**kwargs)
    except RestconfError as exc:
        raise McpToolError(str(exc)) from exc
