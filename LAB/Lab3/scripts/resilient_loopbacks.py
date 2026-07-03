#!/usr/bin/env python3
"""Add bounded retries, status-aware flow control, and metrics."""

from __future__ import annotations

import argparse
import logging
import sys

from src.errors import (
    AuthenticationError,
    AuthorizationError,
    RESTCONFError,
    ResourceNotFoundError,
)
from src.interfaces import INTERFACES_PATH, normalize_interfaces, select_lab_loopbacks
from src.pagination import paginate
from src.reporting import print_interfaces
from src.restconf import ResilientRESTCONFClient
from src.settings import Settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-not-found", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    settings = Settings.from_env()
    client = ResilientRESTCONFClient(settings)
    try:
        if args.demo_not_found:
            try:
                client.get_interface("Loopback999999")
            except ResourceNotFoundError as exc:
                print(f"Controlled 404: {exc}")
                print("Policy: do not retry this missing resource; continue collection.\n")

        index_payload = client.get_json(INTERFACES_PATH)
        index = select_lab_loopbacks(normalize_interfaces(index_payload))
        collected = []

        for page in paginate(index, 20):
            page_records = []
            for summary in page.items:
                try:
                    payload = client.get_interface(summary["interface"])
                except ResourceNotFoundError as exc:
                    logging.warning("Interface disappeared during collection: %s", exc)
                    continue
                page_records.extend(normalize_interfaces(payload))
            collected.extend(page_records)
            print_interfaces(
                page_records,
                f"Resilient page {page.number}/{page.total_pages}",
            )

    except (AuthenticationError, AuthorizationError) as exc:
        print(f"UNRECOVERABLE AUTHORIZATION FAILURE: {exc}", file=sys.stderr)
        print("Collection stopped; correct identity or permissions.", file=sys.stderr)
        return 2
    except RESTCONFError as exc:
        print(f"COLLECTION FAILED AFTER CONTROLLED HANDLING: {exc}", file=sys.stderr)
        return 1

    print(f"\nCollected {len(collected)} loopbacks")
    print(f"HTTP attempts: {client.metrics.attempts}")
    print(f"Retries: {client.metrics.retries}")
    print(f"Responses by status: {client.metrics.responses_by_status}")
    if client.pacer:
        print(f"Client pacing wait: {client.pacer.total_wait_seconds:.2f} seconds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
