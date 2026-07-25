from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


SYSTEM_PROMPT = """
You are a professional network automation assistant for a Cisco IOS XE lab.
Answer only from the supplied MCP-provided RESTCONF route data.
If the supplied data does not contain the requested detail, say what is missing.
Do not invent routes, metrics, protocols, next hops, or device state.
Use concise operational language suitable for a CCNP-level network engineer.
""".strip()


class LlmProviderError(RuntimeError):
    """Raised when the selected LLM provider cannot return a usable answer."""


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    model: str
    location: str


def _prompt(question: str, context: dict[str, Any]) -> str:
    return (
        "Question:\n"
        f"{question}\n\n"
        "MCP-provided RESTCONF route data:\n"
        f"{json.dumps(context, indent=2)}"
    )


def get_provider_info() -> ProviderInfo:
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        return ProviderInfo(
            name="Ollama",
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            location="local",
        )
    if provider == "openai":
        return ProviderInfo(
            name="OpenAI",
            model=os.getenv("OPENAI_MODEL", "").strip() or "not configured",
            location="cloud",
        )
    if provider == "anthropic":
        return ProviderInfo(
            name="Anthropic",
            model=os.getenv("ANTHROPIC_MODEL", "").strip() or "not configured",
            location="cloud",
        )

    raise LlmProviderError(
        "LLM_PROVIDER must be one of: ollama, openai, or anthropic."
    )


def _request_json(
    *,
    url: str,
    headers: dict[str, str] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise LlmProviderError(f"LLM request failed: {exc}") from exc
    except ValueError as exc:
        raise LlmProviderError("The LLM provider returned invalid JSON.") from exc


def _ask_ollama(question: str, context: dict[str, Any]) -> str:
    base_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _prompt(question, context)},
        ],
        "options": {"temperature": 0.1, "top_p": 0.9},
    }
    data = _request_json(url=f"{base_url}/api/chat", headers=None, payload=payload)
    answer = data.get("message", {}).get("content", "")
    if not answer:
        raise LlmProviderError("Ollama returned no answer text.")
    return str(answer)


def _openai_output_text(data: dict[str, Any]) -> str:
    if data.get("output_text"):
        return str(data["output_text"])

    fragments: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                fragments.append(str(content["text"]))
    return "\n".join(fragments)


def _ask_openai(question: str, context: dict[str, Any]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not api_key or not model:
        raise LlmProviderError(
            "OPENAI_API_KEY and OPENAI_MODEL are required when "
            "LLM_PROVIDER=openai."
        )

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": model,
        "instructions": SYSTEM_PROMPT,
        "input": _prompt(question, context),
        "max_output_tokens": int(os.getenv("LLM_MAX_TOKENS", "800")),
    }
    data = _request_json(
        url=f"{base_url}/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload=payload,
    )
    answer = _openai_output_text(data)
    if not answer:
        raise LlmProviderError("OpenAI returned no answer text.")
    return answer


def _ask_anthropic(question: str, context: dict[str, Any]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "").strip()
    if not api_key or not model:
        raise LlmProviderError(
            "ANTHROPIC_API_KEY and ANTHROPIC_MODEL are required when "
            "LLM_PROVIDER=anthropic."
        )

    base_url = os.getenv(
        "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"
    ).rstrip("/")
    payload = {
        "model": model,
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "800")),
        "temperature": 0.1,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": _prompt(question, context)}],
    }
    data = _request_json(
        url=f"{base_url}/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": os.getenv(
                "ANTHROPIC_VERSION", "2023-06-01"
            ),
            "Content-Type": "application/json",
        },
        payload=payload,
    )
    fragments = [
        str(block["text"])
        for block in data.get("content", [])
        if block.get("type") == "text" and block.get("text")
    ]
    answer = "\n".join(fragments)
    if not answer:
        raise LlmProviderError("Anthropic returned no answer text.")
    return answer


def ask_llm(question: str, context: dict[str, Any]) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        return _ask_ollama(question, context)
    if provider == "openai":
        return _ask_openai(question, context)
    if provider == "anthropic":
        return _ask_anthropic(question, context)

    raise LlmProviderError(
        "LLM_PROVIDER must be one of: ollama, openai, or anthropic."
    )
