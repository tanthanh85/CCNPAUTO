"""Minimal disk cache for HTTP validator metadata and JSON representations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ConditionalCache:
    path: Path
    etag: str | None = None
    last_modified: str | None = None
    payload: dict[str, Any] | None = None

    @classmethod
    def load(cls, path: Path) -> "ConditionalCache":
        if not path.exists():
            return cls(path=path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            path=path,
            etag=data.get("etag"),
            last_modified=data.get("last_modified"),
            payload=data.get("payload"),
        )

    @property
    def conditional_headers(self) -> dict[str, str]:
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag
        if self.last_modified:
            headers["If-Modified-Since"] = self.last_modified
        return headers

    def save(self, payload: dict[str, Any], headers: dict[str, str]) -> bool:
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        cache_control = normalized_headers.get("cache-control", "").lower()
        if "no-store" in cache_control:
            return False
        etag = normalized_headers.get("etag")
        last_modified = normalized_headers.get("last-modified")
        if not etag and not last_modified:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "etag": etag,
                    "last_modified": last_modified,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.etag = etag
        self.last_modified = last_modified
        self.payload = payload
        return True
