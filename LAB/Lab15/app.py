from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from mcp_client import McpToolError, call_route_tool


load_dotenv()

app = Flask(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


SYSTEM_PROMPT = """
You are a professional network automation assistant for a Cisco IOS XE lab.
Answer only from the supplied MCP-provided RESTCONF route data.
If the supplied data does not contain the requested detail, say what is missing.
Do not invent routes, metrics, protocols, next hops, or device state.
Use concise operational language suitable for a CCNP-level network engineer.
"""


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


def ask_ollama(question: str, context: dict[str, Any]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Question:\n"
                    f"{question}\n\n"
                    "MCP-provided RESTCONF route data:\n"
                    f"{json.dumps(context, indent=2)}"
                ),
            },
        ],
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    data = response.json()
    return data.get("message", {}).get("content", "No response returned by Ollama.")


@app.get("/")
def index():
    return render_template("index.html", model=OLLAMA_MODEL)


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
        answer = ask_ollama(question, context)
        return jsonify({"ok": True, "answer": answer, "context": context})
    except McpToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5050"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
