from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from logging_config import configure_logging
from restconf_routes import get_routes, route_detail, route_summary, routes_by_protocol


logger = logging.getLogger(__name__)
mcp = FastMCP("ccnpauto-route-assistant")


def route_tool_summary() -> dict[str, Any]:
    logger.info("Executing MCP route summary tool")
    result = route_summary()
    logger.info("MCP route summary completed route_count=%s", result.get("route_count"))
    return result


def route_tool_by_protocol(protocol: str) -> dict[str, Any]:
    logger.info("Executing MCP protocol tool protocol=%s", protocol)
    result = routes_by_protocol(protocol)
    logger.info(
        "MCP protocol tool completed protocol=%s matched_count=%s",
        protocol,
        result.get("matched_count"),
    )
    return result


def route_tool_detail(prefix: str) -> dict[str, Any]:
    logger.info("Executing MCP route detail tool prefix=%s", prefix)
    result = route_detail(prefix)
    logger.info(
        "MCP route detail completed prefix=%s matched_count=%s",
        prefix,
        result.get("matched_count"),
    )
    return result


def route_tool_all() -> dict[str, Any]:
    logger.info("Executing MCP all-routes tool")
    result = get_routes()
    logger.info("MCP all-routes completed route_count=%s", result.get("route_count"))
    return result


@mcp.tool()
def get_route_summary() -> dict[str, Any]:
    """Return the total route count and route counts grouped by protocol."""
    return route_tool_summary()


@mcp.tool()
def get_routes_by_protocol(protocol: str) -> dict[str, Any]:
    """Return routes whose protocol matches static, connected, local, ospf, or another value."""
    return route_tool_by_protocol(protocol)


@mcp.tool()
def get_route_detail(prefix: str) -> dict[str, Any]:
    """Return route details for one exact destination prefix, such as 10.10.10.0/24."""
    return route_tool_detail(prefix)


@mcp.tool()
def get_all_routes() -> dict[str, Any]:
    """Return all normalized routes collected from IOS XE through RESTCONF."""
    return route_tool_all()


if __name__ == "__main__":
    configure_logging("fastmcp_route_server")
    logger.info("Starting FastMCP route server")
    mcp.run()
