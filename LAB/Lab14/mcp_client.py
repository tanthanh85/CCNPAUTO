from __future__ import annotations

import logging
from typing import Any

from mcp_server import (
    route_tool_all,
    route_tool_by_protocol,
    route_tool_detail,
    route_tool_summary,
)
from restconf_routes import RestconfError


logger = logging.getLogger(__name__)


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
        logger.error("Unsupported MCP route tool requested tool=%s", tool_name)
        raise ValueError(f"Unsupported MCP route tool: {tool_name}")

    logger.info("Calling MCP tool=%s arguments=%s", tool_name, kwargs)
    try:
        result = tools[tool_name](**kwargs)
        logger.info(
            "MCP tool completed tool=%s result_keys=%s",
            tool_name,
            sorted(result),
        )
        logger.debug("MCP tool result tool=%s result=%s", tool_name, result)
        return result
    except RestconfError as exc:
        logger.exception("MCP tool failed tool=%s", tool_name)
        raise McpToolError(str(exc)) from exc
