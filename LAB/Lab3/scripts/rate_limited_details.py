#!/usr/bin/env python3

import time

from src.common import (
    INTERFACES_PATH,
    get_interface_json,
    get_json,
    load_settings,
    make_pages,
    make_session,
    normalize_interfaces,
    print_interfaces,
    select_lab_loopbacks,
    wait_for_rate_limit,
)


settings = load_settings()
session = make_session(settings)
index = get_json(session, settings, INTERFACES_PATH)
loopbacks = select_lab_loopbacks(normalize_interfaces(index))

last_request = 0
total_wait = 0
request_count = 0
start_time = time.monotonic()

for page_number, page in enumerate(make_pages(loopbacks, 20), start=1):
    details = []

    for loopback in page:
        last_request, wait_time = wait_for_rate_limit(last_request, settings["rate"])
        total_wait += wait_time

        payload = get_interface_json(session, settings, loopback["interface"])
        details.extend(normalize_interfaces(payload))
        request_count += 1

    print_interfaces(details, f"Rate-limited page {page_number}")

elapsed = time.monotonic() - start_time
print(f"\nRequests: {request_count}")
print(f"Configured rate: {settings['rate']} requests/second")
print(f"Elapsed time: {elapsed:.2f} seconds")
print(f"Observed average: {request_count / elapsed:.2f} requests/second")
print(f"Time spent waiting: {total_wait:.2f} seconds")
