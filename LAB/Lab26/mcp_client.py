from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


logger = logging.getLogger(__name__)


class McpClientError(RuntimeError):
    """Raised when MCP discovery, validation, or execution fails."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]

    def as_llm_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class McpRouteSession:
    def __init__(self, session: ClientSession) -> None:
        self.session = session

    async def list_tools(self) -> list[ToolDefinition]:
        response = await self.session.list_tools()
        tools = [
            ToolDefinition(
                name=tool.name,
                description=tool.description or "",
                input_schema=dict(tool.inputSchema),
            )
            for tool in response.tools
        ]
        logger.info("Discovered MCP tools names=%s", [tool.name for tool in tools])
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        logger.info("Calling MCP tool=%s arguments=%s", name, arguments)
        result = await self.session.call_tool(name, arguments)
        if getattr(result, "isError", False):
            text = " ".join(
                str(getattr(item, "text", ""))
                for item in result.content
                if getattr(item, "text", "")
            )
            raise McpClientError(f"MCP tool {name} failed: {text or 'unknown error'}")

        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict):
            return structured

        for item in result.content:
            text = getattr(item, "text", None)
            if text:
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
        raise McpClientError(f"MCP tool {name} returned no structured dictionary")


@asynccontextmanager
async def open_mcp_route_session() -> AsyncIterator[McpRouteSession]:
    root = Path(__file__).resolve().parent
    server = root / "mcp_server.py"
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(server)],
        env=os.environ.copy(),
    )
    logger.info("Opening MCP stdio session server=%s", server)
    try:
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield McpRouteSession(session)
    except McpClientError:
        raise
    except Exception as exc:
        logger.exception("MCP stdio session failed")
        raise McpClientError(f"MCP session failed: {exc}") from exc
