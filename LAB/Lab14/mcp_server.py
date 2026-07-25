from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from restconf_routes import get_routes, route_detail, route_summary, routes_by_protocol


mcp = FastMCP("ccnpauto-route-assistant")


def route_tool_summary() -> dict[str, Any]:
    return route_summary()


def route_tool_by_protocol(protocol: str) -> dict[str, Any]:
    return routes_by_protocol(protocol)


def route_tool_detail(prefix: str) -> dict[str, Any]:
    return route_detail(prefix)


def route_tool_all() -> dict[str, Any]:
    return get_routes()


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
    mcp.run()
