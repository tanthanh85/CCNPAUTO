#!/usr/bin/env python3

import argparse
from urllib.parse import quote

from src.common import (
    INTERFACES_PATH,
    INTERFACE_PATH,
    load_settings,
    make_pages,
    make_session,
    normalize_interfaces,
    print_interfaces,
    select_lab_loopbacks,
    wait_for_rate_limit,
)
from src.simple_retry import get_json_with_retry


parser = argparse.ArgumentParser()
parser.add_argument("--demo-not-found", action="store_true")
args = parser.parse_args()

settings = load_settings()
session = make_session(settings)
statistics = {"attempts": 0, "retries": 0, "status_codes": {}}
last_request = 0
total_wait = 0

if args.demo_not_found:
    path = INTERFACE_PATH.format("Loopback999999")
    payload, result = get_json_with_retry(session, settings, path, statistics)
    print(f"404 demonstration result: {result}\n")

payload, result = get_json_with_retry(session, settings, INTERFACES_PATH, statistics)
if result != "ok":
    raise SystemExit("Could not retrieve the interface collection")

loopbacks = select_lab_loopbacks(normalize_interfaces(payload))
collected = []

for page_number, page in enumerate(make_pages(loopbacks, 20), start=1):
    page_details = []

    for loopback in page:
        last_request, wait_time = wait_for_rate_limit(last_request, settings["rate"])
        total_wait += wait_time

        name = quote(loopback["interface"], safe="")
        path = INTERFACE_PATH.format(name)
        detail, result = get_json_with_retry(session, settings, path, statistics)

        if result == "ok":
            page_details.extend(normalize_interfaces(detail))
        elif result == "not_found":
            print(f"Skipping {loopback['interface']} because it disappeared")
        elif result == "fatal":
            raise SystemExit("Stopping because credentials or permissions are invalid")
        else:
            raise SystemExit(f"Stopping after repeated failure on {loopback['interface']}")

    collected.extend(page_details)
    print_interfaces(page_details, f"Resilient page {page_number}")

print(f"\nCollected: {len(collected)}")
print(f"HTTP attempts: {statistics['attempts']}")
print(f"Retries: {statistics['retries']}")
print(f"Status codes: {statistics['status_codes']}")
print(f"Rate-limit waiting: {total_wait:.2f} seconds")
