"""Discover and call the local MCP server without using an LLM."""

import asyncio
from pathlib import Path

from fastmcp import Client


async def main() -> None:
    server = str(Path(__file__).with_name("mcp_server.py"))
    async with Client(server) as client:
        tools = await client.list_tools()
        print("Discovered tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        result = await client.call_tool("get_route_summary", {})
        print("\nTool result:")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())

