from __future__ import annotations

import ipaddress
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from logging_config import configure_logging
from restconf_ospf import ospf_operational_status
from restconf_routes import get_routes, route_detail, route_summary, routes_by_protocol


logger = logging.getLogger(__name__)
mcp = FastMCP("ccnpauto-dynamic-route-tools", log_level="WARNING")
ALLOWED_PROTOCOLS = {"static", "connected", "local", "ospf", "eigrp", "bgp", "rip", "isis"}


@mcp.tool()
def get_route_summary() -> dict[str, Any]:
    """Return total IPv4 route count and counts grouped by routing protocol."""
    logger.info("MCP tool started tool=get_route_summary")
    result = route_summary()
    logger.info("MCP tool completed tool=get_route_summary route_count=%s", result.get("route_count"))
    return result


@mcp.tool()
def get_routes_by_protocol(protocol: str) -> dict[str, Any]:
    """Return IPv4 routes for one protocol: static, connected, local, OSPF, EIGRP, BGP, RIP, or IS-IS."""
    normalized = protocol.strip().lower()
    if normalized not in ALLOWED_PROTOCOLS:
        raise ValueError(f"Unsupported protocol. Choose one of: {sorted(ALLOWED_PROTOCOLS)}")
    logger.info("MCP tool started tool=get_routes_by_protocol protocol=%s", normalized)
    result = routes_by_protocol(normalized)
    logger.info("MCP tool completed tool=get_routes_by_protocol matched=%s", result.get("matched_count"))
    return result


@mcp.tool()
def get_route_detail(prefix: str) -> dict[str, Any]:
    """Return the route for one exact IPv4 prefix written in CIDR notation, such as 0.0.0.0/0."""
    network = ipaddress.ip_network(prefix.strip(), strict=False)
    if network.version != 4:
        raise ValueError("This lab accepts IPv4 prefixes only")
    normalized = str(network)
    logger.info("MCP tool started tool=get_route_detail prefix=%s", normalized)
    result = route_detail(normalized)
    logger.info("MCP tool completed tool=get_route_detail matched=%s", result.get("matched_count"))
    return result


@mcp.tool()
def get_all_routes() -> dict[str, Any]:
    """Return all normalized IPv4 routes when the question genuinely requires the complete table."""
    logger.info("MCP tool started tool=get_all_routes")
    result = get_routes()
    logger.info("MCP tool completed tool=get_all_routes route_count=%s", result.get("route_count"))
    return result


@mcp.tool()
def get_ospf_operational_status() -> dict[str, Any]:
    """Return bounded OSPF process, area, interface, neighbor, and state evidence."""
    logger.info("MCP tool started tool=get_ospf_operational_status")
    result = ospf_operational_status()
    logger.info(
        "MCP tool completed tool=get_ospf_operational_status processes=%s neighbors=%s",
        result.get("process_count"),
        result.get("neighbor_count"),
    )
    return result


if __name__ == "__main__":
    configure_logging("lab27_mcp_server")
    logger.info("Starting FastMCP server over stdio")
    mcp.run()
