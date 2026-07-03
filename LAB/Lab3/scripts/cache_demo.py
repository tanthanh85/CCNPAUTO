#!/usr/bin/env python3

import json
from pathlib import Path

from src.common import load_settings, make_session


PATH = "/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback?content=config"
CACHE_FILE = Path(".cache/loopbacks.json")

settings = load_settings()
session = make_session(settings)

# Load ETag or Last-Modified from the previous run, if available.
cache = {}
if CACHE_FILE.exists():
    cache = json.loads(CACHE_FILE.read_text())

headers = {}
if cache.get("etag"):
    headers["If-None-Match"] = cache["etag"]
if cache.get("last_modified"):
    headers["If-Modified-Since"] = cache["last_modified"]

response = session.get(
    settings["base_url"] + PATH,
    headers=headers,
    timeout=(settings["connect_timeout"], settings["read_timeout"]),
)

print("HTTP status:", response.status_code)
print("Cache-Control:", response.headers.get("Cache-Control", "<absent>"))
print("ETag:", response.headers.get("ETag", "<absent>"))
print("Last-Modified:", response.headers.get("Last-Modified", "<absent>"))

if response.status_code == 304:
    print("The resource did not change. The saved payload can be reused.")
elif response.status_code == 200:
    payload = response.json()
    cache_control = response.headers.get("Cache-Control", "").lower()
    etag = response.headers.get("ETag")
    last_modified = response.headers.get("Last-Modified")

    if "no-store" in cache_control:
        print("The server prohibited storage. Nothing was cached.")
    elif etag or last_modified:
        CACHE_FILE.parent.mkdir(exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps(
                {
                    "etag": etag,
                    "last_modified": last_modified,
                    "payload": payload,
                },
                indent=2,
            )
        )
        print("Saved the payload and HTTP validator for the next run.")
    else:
        print("No ETag or Last-Modified header was returned. Nothing was cached.")
else:
    print("The optional cache request was not supported by this sandbox image.")
