from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from logging_config import configure_logging
from mcp_client import McpClientError
from tool_agent import ToolAgentError, ToolCallingModel, discover_tools, run_dynamic_agent


load_dotenv()
configure_logging("lab26_dynamic_tool_assistant")
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.get("/")
def index():
    provider = ToolCallingModel().info
    return render_template(
        "index.html",
        provider=provider.name,
        model=provider.model,
        location=provider.location,
    )


@app.get("/api/tools")
def api_tools():
    try:
        tools = asyncio.run(discover_tools())
        return jsonify({"ok": True, "tools": tools})
    except (McpClientError, ToolAgentError) as exc:
        logger.exception("MCP tool discovery failed")
        return jsonify({"ok": False, "error": str(exc)}), 502


@app.post("/api/chat")
def api_chat():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()
    if not question:
        return jsonify({"ok": False, "error": "Question is required."}), 400
    if len(question) > 1000:
        return jsonify({"ok": False, "error": "Question must not exceed 1000 characters."}), 400

    logger.info("Chat request received characters=%d", len(question))
    try:
        result = asyncio.run(run_dynamic_agent(question))
        return jsonify({"ok": True, **result})
    except (McpClientError, ToolAgentError) as exc:
        logger.exception("Dynamic tool agent failed")
        return jsonify({"ok": False, "error": str(exc)}), 502


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5056")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
