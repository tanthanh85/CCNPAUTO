"""Local API used to practise pagination and HTTP 429 recovery."""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, url_for


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
RATE_LIMIT = 8
RATE_WINDOW_SECONDS = 1.0

app = Flask(__name__)
request_times: deque[float] = deque()
rate_lock = threading.Lock()


def configure_logging() -> None:
    """Create a new server log file every time the process starts."""
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = LOG_DIR / f"server_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    app.logger.info("API server logging initialized file=%s", log_path)


def build_interfaces() -> list[dict[str, object]]:
    """Return deterministic interface records for a fictional IOS XE router."""
    return [
        {
            "id": number,
            "device": "edge-router-01",
            "name": f"Loopback{number}",
            "ipv4": f"192.0.2.{number}/32",
            "status": "up",
            "description": f"Automation-managed service interface {number}",
        }
        for number in range(1, 101)
    ]


INTERFACES = build_interfaces()


def parse_positive_integer(name: str, default: int, maximum: int) -> int:
    """Validate a positive integer query parameter."""
    raw_value = request.args.get(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if value < 1 or value > maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return value


def pagination_response():
    """Build a page of records plus metadata and navigation links."""
    try:
        page = parse_positive_integer("page", default=1, maximum=10_000)
        per_page = parse_positive_integer("per_page", default=20, maximum=50)
    except ValueError as exc:
        app.logger.warning(
            "Rejected pagination parameters query=%s reason=%s",
            request.query_string.decode(),
            exc,
        )
        return jsonify({"error": "invalid_request", "message": str(exc)}), 400

    total_items = len(INTERFACES)
    total_pages = math.ceil(total_items / per_page)
    start = (page - 1) * per_page
    records = INTERFACES[start : start + per_page]

    def page_url(target_page: int) -> str:
        return url_for(
            request.endpoint,
            page=target_page,
            per_page=per_page,
            _external=True,
        )

    links = {
        "self": page_url(page),
        "next": page_url(page + 1) if page < total_pages else None,
        "previous": page_url(page - 1) if page > 1 else None,
    }
    body = {
        "data": records,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
        "links": links,
    }

    response = jsonify(body)
    response.headers["X-Total-Count"] = str(total_items)
    link_values = []
    if links["next"]:
        link_values.append(f'<{links["next"]}>; rel="next"')
    if links["previous"]:
        link_values.append(f'<{links["previous"]}>; rel="previous"')
    if link_values:
        response.headers["Link"] = ", ".join(link_values)

    app.logger.info(
        "Returned interface page endpoint=%s page=%d per_page=%d records=%d",
        request.endpoint,
        page,
        per_page,
        len(records),
    )
    return response


def rate_limit_response():
    """Return a 429 response when the fixed-window allowance is exhausted."""
    now = time.monotonic()
    with rate_lock:
        while request_times and now - request_times[0] >= RATE_WINDOW_SECONDS:
            request_times.popleft()

        if len(request_times) >= RATE_LIMIT:
            retry_after = max(
                1,
                math.ceil(RATE_WINDOW_SECONDS - (now - request_times[0])),
            )
            app.logger.warning(
                "Rate limit exceeded active_requests=%d retry_after=%d",
                len(request_times),
                retry_after,
            )
            response = jsonify(
                {
                    "error": "rate_limit_exceeded",
                    "message": "Request frequency exceeded the lab policy.",
                    "retry_after_seconds": retry_after,
                }
            )
            response.status_code = 429
            response.headers["Retry-After"] = str(retry_after)
            return response

        request_times.append(now)
    return None


@app.get("/api/interfaces")
def get_interfaces():
    """Return paginated data without rate limiting."""
    return pagination_response()


@app.get("/api/limited/interfaces")
def get_limited_interfaces():
    """Return paginated data subject to the lab rate limit."""
    limited = rate_limit_response()
    if limited is not None:
        return limited
    return pagination_response()


@app.post("/admin/reset")
def reset_rate_limiter():
    """Reset the in-memory limiter between learner test runs."""
    with rate_lock:
        request_times.clear()
    app.logger.info("Rate limiter reset by local learner request")
    return jsonify({"status": "reset"}), 200


if __name__ == "__main__":
    configure_logging()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)

