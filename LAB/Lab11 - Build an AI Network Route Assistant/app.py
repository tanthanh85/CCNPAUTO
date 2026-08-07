from __future__ import annotations

import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from llm_providers import (
    LlmProviderError,
    ask_llm,
    get_provider_info,
)
from logging_config import configure_logging
from mcp_client import McpToolError, call_route_tool


load_dotenv()
configure_logging("flask_ai_route_assistant")
logger = logging.getLogger(__name__)

app = Flask(__name__)


def choose_route_context(question: str) -> dict[str, Any]:
    text = question.lower()
    logger.debug(
        "Selecting MCP route context question_characters=%d",
        len(question),
    )

    if "static" in text:
        logger.info("Selected MCP tool=get_routes_by_protocol protocol=static")
        return call_route_tool("get_routes_by_protocol", protocol="static")
    if "connected" in text or "directly connected" in text:
        logger.info("Selected MCP tool=get_routes_by_protocol protocol=connected")
        return call_route_tool("get_routes_by_protocol", protocol="connected")
    if "local" in text:
        logger.info("Selected MCP tool=get_routes_by_protocol protocol=local")
        return call_route_tool("get_routes_by_protocol", protocol="local")
    if "ospf" in text:
        logger.info("Selected MCP tool=get_routes_by_protocol protocol=ospf")
        return call_route_tool("get_routes_by_protocol", protocol="ospf")

    words = [word.strip(" ,.?") for word in question.split()]
    prefixes = [word for word in words if "/" in word and any(char.isdigit() for char in word)]
    if prefixes:
        logger.info("Selected MCP tool=get_route_detail prefix=%s", prefixes[0])
        return call_route_tool("get_route_detail", prefix=prefixes[0])

    if "how many" in text or "number" in text or "count" in text or "summary" in text:
        logger.info("Selected MCP tool=get_route_summary")
        return call_route_tool("get_route_summary")

    logger.info("Selected MCP tool=get_all_routes")
    return call_route_tool("get_all_routes")


@app.get("/")
def index():
    provider = get_provider_info()
    logger.info(
        "Rendering assistant UI provider=%s model=%s location=%s",
        provider.name,
        provider.model,
        provider.location,
    )
    return render_template(
        "index.html",
        provider=provider.name,
        model=provider.model,
        location=provider.location,
    )


@app.get("/api/summary")
def api_summary():
    logger.info("Received route summary request remote_address=%s", request.remote_addr)
    try:
        data = call_route_tool("get_route_summary")
        logger.info("Route summary request completed route_count=%s", data.get("route_count"))
        return jsonify({"ok": True, "data": data})
    except McpToolError as exc:
        logger.exception("Route summary MCP tool failed")
        return jsonify({"ok": False, "error": str(exc)}), 502


@app.post("/api/chat")
def api_chat():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()

    if not question:
        logger.warning("Rejected chat request because question was empty")
        return jsonify({"ok": False, "error": "Question is required."}), 400

    logger.info(
        "Received chat request remote_address=%s question_characters=%d",
        request.remote_addr,
        len(question),
    )
    try:
        context = choose_route_context(question)
        logger.debug(
            "MCP context keys=%s serialized_characters=%d",
            sorted(context),
            len(str(context)),
        )
        started = time.perf_counter()
        answer = ask_llm(question, context)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        provider = get_provider_info()
        logger.info(
            "Chat request completed provider=%s model=%s "
            "elapsed_ms=%d answer_characters=%d",
            provider.name,
            provider.model,
            elapsed_ms,
            len(answer),
        )
        return jsonify(
            {
                "ok": True,
                "answer": answer,
                "context": context,
                "provider": provider.name,
                "model": provider.model,
                "location": provider.location,
                "elapsed_ms": elapsed_ms,
            }
        )
    except McpToolError as exc:
        logger.exception("Chat request failed while collecting MCP route context")
        return jsonify({"ok": False, "error": str(exc)}), 502
    except LlmProviderError as exc:
        logger.exception("Chat request failed in LLM provider")
        return jsonify({"ok": False, "error": str(exc)}), 502


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5050"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(
        "Starting Flask assistant host=%s port=%d debug=%s",
        host,
        port,
        debug,
    )
    app.run(host=host, port=port, debug=debug)
