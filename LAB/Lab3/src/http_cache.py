"""Save and reuse HTTP ETag or Last-Modified values."""

import json
from pathlib import Path


class HTTPCache:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {}

        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    def conditional_headers(self):
        headers = {}
        if self.data.get("etag"):
            headers["If-None-Match"] = self.data["etag"]
        if self.data.get("last_modified"):
            headers["If-Modified-Since"] = self.data["last_modified"]
        return headers

    def save(self, payload, response_headers):
        cache_control = response_headers.get("Cache-Control", "").lower()
        etag = response_headers.get("ETag")
        last_modified = response_headers.get("Last-Modified")

        if "no-store" in cache_control or (not etag and not last_modified):
            return False

        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "etag": etag,
                    "last_modified": last_modified,
                    "payload": payload,
                },
                indent=2,
            )
        )
        return True
