"""Meaningful exceptions used for RESTCONF flow control."""

from __future__ import annotations


class RESTCONFError(RuntimeError):
    """Base class for controlled RESTCONF failures."""


class TransportError(RESTCONFError):
    """Connection, TLS, DNS, or timeout failure after bounded retries."""


class ResponseDecodeError(RESTCONFError):
    """The server returned a successful response that was not valid JSON."""


class HTTPStatusError(RESTCONFError):
    def __init__(self, status: int, path: str, detail: str) -> None:
        self.status = status
        self.path = path
        self.detail = detail
        super().__init__(f"HTTP {status} for {path}: {detail}")


class AuthenticationError(HTTPStatusError):
    """HTTP 401: credentials are missing or invalid; do not retry."""


class AuthorizationError(HTTPStatusError):
    """HTTP 403: identity lacks permission; do not retry."""


class ResourceNotFoundError(HTTPStatusError):
    """HTTP 404: target resource does not exist."""


class RateLimitError(HTTPStatusError):
    """HTTP 429 remained after bounded Retry-After processing."""


class ServerError(HTTPStatusError):
    """A retryable 5xx status remained after bounded retries."""
