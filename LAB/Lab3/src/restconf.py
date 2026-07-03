"""Basic and resilient RESTCONF clients used progressively in Lab 3."""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote

import requests
import urllib3

from src.errors import (
    AuthenticationError,
    AuthorizationError,
    HTTPStatusError,
    RateLimitError,
    ResourceNotFoundError,
    ResponseDecodeError,
    ServerError,
    TransportError,
)
from src.interfaces import INTERFACE_PATH
from src.rate_limit import RequestPacer
from src.settings import Settings


LOG = logging.getLogger(__name__)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER_SECONDS = 60.0


@dataclass
class APIResponse:
    status: int
    payload: dict[str, Any] | None
    headers: dict[str, str]


@dataclass
class ClientMetrics:
    attempts: int = 0
    retries: int = 0
    responses_by_status: dict[int, int] = field(default_factory=dict)

    def record_status(self, status: int) -> None:
        self.responses_by_status[status] = self.responses_by_status.get(status, 0) + 1


class BasicRESTCONFClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = (settings.username, settings.password)
        self.session.headers.update({"Accept": "application/yang-data+json"})
        self.session.verify = settings.verify_tls
        if not settings.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_json(self, path: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.settings.base_url}{path}",
            timeout=(self.settings.connect_timeout, self.settings.read_timeout),
        )
        response.raise_for_status()
        return response.json()

    def get_interface(self, name: str) -> dict[str, Any]:
        path = INTERFACE_PATH.format(name=quote(name, safe=""))
        return self.get_json(path)


class ResilientRESTCONFClient(BasicRESTCONFClient):
    def __init__(self, settings: Settings, *, paced: bool = True) -> None:
        super().__init__(settings)
        self.pacer = RequestPacer(settings.requests_per_second) if paced else None
        self.metrics = ClientMetrics()

    @staticmethod
    def _error_detail(response: requests.Response) -> str:
        try:
            body = response.json()
        except requests.JSONDecodeError:
            return response.text.strip()[:500] or response.reason
        return json.dumps(body, separators=(",", ":"))[:500]

    @staticmethod
    def _retry_after_seconds(response: requests.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError):
                return None

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(8.0, 0.5 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.25)

    def get(
        self,
        path: str,
        *,
        conditional_headers: dict[str, str] | None = None,
        allow_not_modified: bool = False,
    ) -> APIResponse:
        attempts_allowed = self.settings.max_retries + 1
        last_transport_error: Exception | None = None

        for attempt in range(1, attempts_allowed + 1):
            if self.pacer is not None:
                self.pacer.wait()
            self.metrics.attempts += 1
            try:
                response = self.session.get(
                    f"{self.settings.base_url}{path}",
                    headers=conditional_headers,
                    timeout=(self.settings.connect_timeout, self.settings.read_timeout),
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_transport_error = exc
                if attempt >= attempts_allowed:
                    break
                self.metrics.retries += 1
                delay = self._backoff(attempt)
                LOG.warning(
                    "Transport failure on attempt %s/%s; retrying in %.2fs: %s",
                    attempt,
                    attempts_allowed,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue

            self.metrics.record_status(response.status_code)
            if response.status_code == 304 and allow_not_modified:
                return APIResponse(304, None, dict(response.headers))
            if 200 <= response.status_code < 300:
                try:
                    payload = response.json() if response.content else None
                except requests.JSONDecodeError as exc:
                    raise ResponseDecodeError(
                        f"Invalid JSON from {path}: {response.text[:200]!r}"
                    ) from exc
                return APIResponse(response.status_code, payload, dict(response.headers))

            detail = self._error_detail(response)
            if response.status_code == 401:
                raise AuthenticationError(401, path, detail)
            if response.status_code == 403:
                raise AuthorizationError(403, path, detail)
            if response.status_code == 404:
                raise ResourceNotFoundError(404, path, detail)

            if response.status_code in RETRYABLE_STATUS and attempt < attempts_allowed:
                self.metrics.retries += 1
                delay = self._retry_after_seconds(response)
                if response.status_code == 429 and delay is not None and delay > MAX_RETRY_AFTER_SECONDS:
                    raise RateLimitError(
                        429,
                        path,
                        f"Retry-After {delay:.0f}s exceeds the client safety limit; {detail}",
                    )
                if delay is None:
                    delay = self._backoff(attempt)
                LOG.warning(
                    "HTTP %s on attempt %s/%s; retrying in %.2fs",
                    response.status_code,
                    attempt,
                    attempts_allowed,
                    delay,
                )
                time.sleep(delay)
                continue

            if response.status_code == 429:
                raise RateLimitError(429, path, detail)
            if response.status_code >= 500:
                raise ServerError(response.status_code, path, detail)
            raise HTTPStatusError(response.status_code, path, detail)

        raise TransportError(
            f"RESTCONF GET {path} failed after {attempts_allowed} attempt(s): "
            f"{last_transport_error}"
        )

    def get_json(self, path: str) -> dict[str, Any]:
        response = self.get(path)
        if response.payload is None:
            raise ResponseDecodeError(f"RESTCONF GET {path} returned no JSON body")
        return response.payload

    def get_interface(self, name: str) -> dict[str, Any]:
        return self.get_json(INTERFACE_PATH.format(name=quote(name, safe="")))
