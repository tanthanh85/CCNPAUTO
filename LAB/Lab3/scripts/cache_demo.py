#!/usr/bin/env python3
"""Optionally demonstrate ETag/Last-Modified conditional RESTCONF GETs."""

from __future__ import annotations

from pathlib import Path

from src.cache import ConditionalCache
from src.errors import RESTCONFError
from src.restconf import ResilientRESTCONFClient
from src.settings import Settings


CONFIG_LOOPBACK_PATH = (
    "/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback?content=config"
)
CACHE_PATH = Path(".cache/loopback-config.json")


def header(headers: dict[str, str], name: str) -> str:
    return next(
        (value for key, value in headers.items() if key.lower() == name.lower()),
        "<absent>",
    )


def fetch(client: ResilientRESTCONFClient, cache: ConditionalCache) -> None:
    response = client.get(
        CONFIG_LOOPBACK_PATH,
        conditional_headers=cache.conditional_headers or None,
        allow_not_modified=True,
    )
    if response.status == 304:
        print("HTTP 304 Not Modified: reused the previously validated local payload.")
        return

    print(f"HTTP {response.status}")
    print("Cache-Control:", header(response.headers, "Cache-Control"))
    print("ETag:", header(response.headers, "ETag"))
    print("Last-Modified:", header(response.headers, "Last-Modified"))
    if response.payload and cache.save(response.payload, response.headers):
        print("Stored payload and validators for conditional revalidation.")
    else:
        print("Server supplied no usable validator or prohibited storage; not cached.")


def main() -> None:
    client = ResilientRESTCONFClient(Settings.from_env(), paced=False)
    cache = ConditionalCache.load(CACHE_PATH)
    try:
        print("First retrieval or revalidation")
        fetch(client, cache)
        print("\nImmediate second retrieval")
        fetch(client, ConditionalCache.load(CACHE_PATH))
    except RESTCONFError as exc:
        print(f"Optional cache exercise unavailable on this resource: {exc}")


if __name__ == "__main__":
    main()
