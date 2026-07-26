from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import requests
import urllib3


logger = logging.getLogger(__name__)


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
    prompt = (
        "Question:\n"
        f"{question}\n\n"
        "MCP-provided RESTCONF route data:\n"
        f"{json.dumps(context, indent=2)}"
    )
    logger.debug(
        "Built grounded prompt question_characters=%d "
        "context_keys=%s prompt_characters=%d",
        len(question),
        sorted(context),
        len(prompt),
    )
    return prompt


def get_provider_info() -> ProviderInfo:
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        info = ProviderInfo(
            name="Ollama",
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            location="local",
        )
        logger.debug("Selected LLM provider=%s model=%s location=%s", info.name, info.model, info.location)
        return info
    if provider == "vllm":
        info = ProviderInfo(
            name="vLLM",
            model=os.getenv("VLLM_MODEL", "Qwen/Qwen3-8B"),
            location="local or private server",
        )
        logger.debug("Selected LLM provider=%s model=%s location=%s", info.name, info.model, info.location)
        return info
    if provider == "openai":
        info = ProviderInfo(
            name="OpenAI",
            model=os.getenv("OPENAI_MODEL", "").strip() or "not configured",
            location="cloud",
        )
        logger.debug("Selected LLM provider=%s model=%s location=%s", info.name, info.model, info.location)
        return info
    if provider == "anthropic":
        info = ProviderInfo(
            name="Anthropic",
            model=os.getenv("ANTHROPIC_MODEL", "").strip() or "not configured",
            location="cloud",
        )
        logger.debug("Selected LLM provider=%s model=%s location=%s", info.name, info.model, info.location)
        return info

    raise LlmProviderError(
        "LLM_PROVIDER must be one of: ollama, vllm, openai, or anthropic."
    )


def _request_json(
    *,
    url: str,
    headers: dict[str, str] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    logger.info(
        "Sending LLM request endpoint=%s timeout_seconds=%s "
        "payload_keys=%s authorization_configured=%s",
        url,
        timeout,
        sorted(payload),
        bool(headers and any(key.lower() in {"authorization", "x-api-key"} for key in headers)),
    )
    started = time.perf_counter()

    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
            verify=False,
        )
        logger.info(
            "LLM HTTP response status=%d elapsed_seconds=%.3f",
            response.status_code,
            time.perf_counter() - started,
        )
        response.raise_for_status()
        data = response.json()
        logger.debug("LLM response top_level_keys=%s", sorted(data))
        return data
    except requests.exceptions.RequestException as exc:
        logger.exception("LLM HTTP request failed endpoint=%s", url)
        raise LlmProviderError(f"LLM request failed: {exc}") from exc
    except ValueError as exc:
        logger.exception("LLM provider returned invalid JSON endpoint=%s", url)
        raise LlmProviderError("The LLM provider returned invalid JSON.") from exc


def _ask_ollama(question: str, context: dict[str, Any]) -> str:
    base_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    logger.info("Calling local Ollama model=%s base_url=%s", model, base_url)
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
    logger.info("Ollama returned answer_characters=%d", len(str(answer)))
    return str(answer)


def _ask_vllm(question: str, context: dict[str, Any]) -> str:
    base_url = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    model = os.getenv("VLLM_MODEL", "Qwen/Qwen3-8B").strip()
    api_key = os.getenv("VLLM_API_KEY", "").strip()
    if not model or not api_key:
        raise LlmProviderError(
            "VLLM_MODEL and VLLM_API_KEY are required when "
            "LLM_PROVIDER=vllm."
        )

    logger.info("Calling vLLM model=%s base_url=%s", model, base_url)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _prompt(question, context)},
        ],
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "800")),
    }
    data = _request_json(
        url=f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload=payload,
    )
    choices = data.get("choices", [])
    answer = (
        choices[0].get("message", {}).get("content", "")
        if choices
        else ""
    )
    if not answer:
        raise LlmProviderError("vLLM returned no answer text.")
    logger.info("vLLM returned answer_characters=%d", len(str(answer)))
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
    logger.info("Calling OpenAI model=%s base_url=%s", model, base_url)
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
    logger.info("OpenAI returned answer_characters=%d", len(answer))
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
    logger.info("Calling Anthropic model=%s base_url=%s", model, base_url)
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
    logger.info("Anthropic returned answer_characters=%d", len(answer))
    return answer


def ask_llm(question: str, context: dict[str, Any]) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    logger.info(
        "Dispatching grounded question to provider=%s context_keys=%s",
        provider,
        sorted(context),
    )

    if provider == "ollama":
        return _ask_ollama(question, context)
    if provider == "vllm":
        return _ask_vllm(question, context)
    if provider == "openai":
        return _ask_openai(question, context)
    if provider == "anthropic":
        return _ask_anthropic(question, context)

    raise LlmProviderError(
        "LLM_PROVIDER must be one of: ollama, vllm, openai, or anthropic."
    )
