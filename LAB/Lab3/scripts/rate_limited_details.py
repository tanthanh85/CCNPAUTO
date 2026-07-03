#!/usr/bin/env python3
"""Retrieve individual loopbacks at a controlled request rate, 20 per page."""

from __future__ import annotations

import time

from src.interfaces import INTERFACES_PATH, normalize_interfaces, select_lab_loopbacks
from src.pagination import paginate
from src.rate_limit import RequestPacer
from src.reporting import print_interfaces
from src.restconf import BasicRESTCONFClient
from src.settings import Settings


def main() -> None:
    settings = Settings.from_env()
    client = BasicRESTCONFClient(settings)
    index = select_lab_loopbacks(normalize_interfaces(client.get_json(INTERFACES_PATH)))
    pacer = RequestPacer(settings.requests_per_second)
    started = time.monotonic()
    request_count = 0

    for page in paginate(index, 20):
        details = []
        for summary in page.items:
            pacer.wait()
            payload = client.get_interface(summary["interface"])
            details.extend(normalize_interfaces(payload))
            request_count += 1
        print_interfaces(
            details,
            f"Rate-limited detail page {page.number}/{page.total_pages}",
        )

    elapsed = time.monotonic() - started
    print(f"\nRequests: {request_count}")
    print(f"Configured maximum: {settings.requests_per_second:.2f} requests/second")
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(f"Observed average: {request_count / elapsed:.2f} requests/second")
    print(f"Time deliberately waiting: {pacer.total_wait_seconds:.2f} seconds")


if __name__ == "__main__":
    main()
