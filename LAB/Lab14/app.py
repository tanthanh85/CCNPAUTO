from __future__ import annotations

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
from mcp_client import McpToolError, call_route_tool


load_dotenv()

app = Flask(__name__)


def choose_route_context(question: str) -> dict[str, Any]:
    text = question.lower()

    if "static" in text:
        return call_route_tool("get_routes_by_protocol", protocol="static")
    if "connected" in text or "directly connected" in text:
        return call_route_tool("get_routes_by_protocol", protocol="connected")
    if "local" in text:
        return call_route_tool("get_routes_by_protocol", protocol="local")
    if "ospf" in text:
        return call_route_tool("get_routes_by_protocol", protocol="ospf")

    words = [word.strip(" ,.?") for word in question.split()]
    prefixes = [word for word in words if "/" in word and any(char.isdigit() for char in word)]
    if prefixes:
        return call_route_tool("get_route_detail", prefix=prefixes[0])

    if "how many" in text or "number" in text or "count" in text or "summary" in text:
        return call_route_tool("get_route_summary")

    return call_route_tool("get_all_routes")


@app.get("/")
def index():
    provider = get_provider_info()
    return render_template(
        "index.html",
        provider=provider.name,
        model=provider.model,
        location=provider.location,
    )


@app.get("/api/summary")
def api_summary():
    try:
        return jsonify({"ok": True, "data": call_route_tool("get_route_summary")})
    except McpToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


@app.post("/api/chat")
def api_chat():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()

    if not question:
        return jsonify({"ok": False, "error": "Question is required."}), 400

    try:
        context = choose_route_context(question)
        started = time.perf_counter()
        answer = ask_llm(question, context)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        provider = get_provider_info()
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
        return jsonify({"ok": False, "error": str(exc)}), 502
    except LlmProviderError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5050"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
