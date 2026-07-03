#!/usr/bin/env python3
"""Local Flask API for pagination, HTTP 429, and cache-control exercises."""

import hashlib
import json
import math
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, make_response, request


class FixedWindowRateLimiter:
    """Allow a fixed number of requests during each time window."""

    def __init__(self, limit=8, window_seconds=1.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.window_started = time.monotonic()
        self.request_count = 0

    def check(self):
        now = time.monotonic()
        elapsed = now - self.window_started

        if elapsed >= self.window_seconds:
            self.window_started = now
            self.request_count = 0
            elapsed = 0

        self.request_count += 1
        remaining = max(0, self.limit - self.request_count)
        reset_after = max(0.0, self.window_seconds - elapsed)
        allowed = self.request_count <= self.limit
        return allowed, remaining, reset_after


def build_dummy_interfaces(count=100):
    return [
        {
            "id": number,
            "name": f"Loopback{number}",
            "ipv4_address": f"198.18.{(number - 1) // 254}.{((number - 1) % 254) + 1}",
            "prefix_length": 32,
            "oper_status": "up",
            "site": f"BRANCH-{((number - 1) % 10) + 1:02d}",
        }
        for number in range(1, count + 1)
    ]


app = Flask(__name__)
interfaces = build_dummy_interfaces()
rate_limiter = FixedWindowRateLimiter(limit=8, window_seconds=1.0)


@app.get("/health")
def health():
    return {"status": "ok", "records": len(interfaces)}


@app.get("/api/interfaces")
def get_interfaces():
    allowed, remaining, reset_after = rate_limiter.check()

    if not allowed:
        response = make_response(
            jsonify(
                {
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests in the current window",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            429,
        )
        response.headers["Retry-After"] = str(max(1, math.ceil(reset_after)))
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.limit)
        response.headers["X-RateLimit-Remaining"] = "0"
        return response

    try:
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "10"))
    except ValueError:
        return {"error": "page and page_size must be integers"}, 400

    if page < 1 or page_size < 1 or page_size > 50:
        return {"error": "page must be >= 1 and page_size must be 1-50"}, 400

    total_pages = math.ceil(len(interfaces) / page_size)
    start = (page - 1) * page_size
    records = interfaces[start : start + page_size]
    payload = {
        "items": records,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": len(interfaces),
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "next_page": page + 1 if page < total_pages else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    etag = hashlib.sha256(json.dumps(payload["items"], sort_keys=True).encode()).hexdigest()
    if request.headers.get("If-None-Match") == f'"{etag}"':
        response = make_response("", 304)
    else:
        response = make_response(jsonify(payload), 200)

    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "private, max-age=30, must-revalidate"
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
