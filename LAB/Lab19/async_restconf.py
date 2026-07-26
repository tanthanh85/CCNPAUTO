#!/usr/bin/env python3
"""Retrieve several IOS XE RESTCONF resources concurrently with trusted TLS."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
from dotenv import load_dotenv


RESOURCES = {
    "hostname": (
        "/restconf/data/Cisco-IOS-XE-native:native/hostname"
    ),
    "interfaces": (
        "/restconf/data/Cisco-IOS-XE-native:native/interface"
    ),
    "interface_state": (
        "/restconf/data/ietf-interfaces:interfaces-state"
    ),
    "cpu_usage": (
        "/restconf/data/Cisco-IOS-XE-process-cpu-oper:cpu-usage"
    ),
}


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("<"):
        raise ValueError(f"Set {name} in .env")
    return value


async def fetch_resource(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    name: str,
    url: str,
) -> dict:
    started = time.perf_counter()
    try:
        async with semaphore:
            async with session.get(url) as response:
                body = await response.text()
                elapsed = round(time.perf_counter() - started, 3)
                if response.status >= 400:
                    return {
                        "name": name,
                        "url": url,
                        "status": response.status,
                        "elapsed_seconds": elapsed,
                        "ok": False,
                        "error": body[:500],
                    }
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError as exc:
                    return {
                        "name": name,
                        "url": url,
                        "status": response.status,
                        "elapsed_seconds": elapsed,
                        "ok": False,
                        "error": f"Invalid JSON: {exc}",
                    }
                return {
                    "name": name,
                    "url": url,
                    "status": response.status,
                    "elapsed_seconds": elapsed,
                    "ok": True,
                    "payload": payload,
                }
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        return {
            "name": name,
            "url": url,
            "status": None,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


async def collect(concurrency: int) -> tuple[list[dict], float]:
    base_url = required("IOSXE_BASE_URL").rstrip("/")
    ca_bundle = Path(required("CA_BUNDLE")).expanduser()
    if not ca_bundle.is_file():
        raise FileNotFoundError(f"CA bundle not found: {ca_bundle}")

    ssl_context = ssl.create_default_context(cafile=str(ca_bundle))
    timeout = aiohttp.ClientTimeout(
        total=float(os.getenv("REQUEST_TIMEOUT", "15"))
    )
    connector = aiohttp.TCPConnector(ssl=ssl_context, limit=concurrency)
    semaphore = asyncio.Semaphore(concurrency)
    auth = aiohttp.BasicAuth(
        required("IOSXE_USERNAME"),
        required("IOSXE_PASSWORD"),
    )

    started = time.perf_counter()
    async with aiohttp.ClientSession(
        auth=auth,
        headers={"Accept": "application/yang-data+json"},
        connector=connector,
        timeout=timeout,
    ) as session:
        tasks = [
            fetch_resource(session, semaphore, name, base_url + path)
            for name, path in RESOURCES.items()
        ]
        results = await asyncio.gather(*tasks)
    return results, round(time.perf_counter() - started, 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        choices=range(1, 9),
    )
    args = parser.parse_args()
    load_dotenv()

    results, elapsed = asyncio.run(collect(args.concurrency))
    output = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "concurrency": args.concurrency,
        "total_elapsed_seconds": elapsed,
        "successful": sum(item["ok"] for item in results),
        "failed": sum(not item["ok"] for item in results),
        "results": results,
    }

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    output_file = output_dir / f"async_restconf_{timestamp}.json"
    output_file.write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Completed {len(results)} requests in {elapsed}s "
        f"with concurrency={args.concurrency}"
    )
    for item in results:
        print(
            f"{item['name']:<16} status={item['status']} "
            f"elapsed={item['elapsed_seconds']}s ok={item['ok']}"
        )
    print(f"Detailed result: {output_file}")


if __name__ == "__main__":
    main()
