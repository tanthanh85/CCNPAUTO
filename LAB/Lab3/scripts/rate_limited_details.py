#!/usr/bin/env python3

import time
import requests

from src.interface_utils import normalize_interfaces, print_interfaces, select_lab_loopbacks
from src.pagination import Paginator
from src.rate_limiter import RateLimiter
from src.restconf_client import APIError, INTERFACES_PATH, RESTCONFClient
from src.settings import Settings


try:
    settings = Settings()
    client = RESTCONFClient(settings)
    limiter = RateLimiter(settings.requests_per_second)

    index = client.get_json(INTERFACES_PATH)
    loopbacks = select_lab_loopbacks(normalize_interfaces(index))
    pages = Paginator(loopbacks, 20).pages()

    request_count = 0
    start_time = time.monotonic()

    for page_number, page in enumerate(pages, start=1):
        details = []

        for loopback in page:
            limiter.wait()
            payload = client.get_interface(loopback["interface"])
            details.extend(normalize_interfaces(payload))
            request_count += 1

        print_interfaces(details, f"Rate-limited page {page_number}")

    elapsed = time.monotonic() - start_time
    print(f"\nRequests: {request_count}")
    print(f"Configured rate: {settings.requests_per_second} requests/second")
    print(f"Observed average: {request_count / elapsed:.2f} requests/second")
    print(f"Time spent waiting: {limiter.total_wait:.2f} seconds")

except requests.Timeout:
    print("A RESTCONF request timed out.")
except requests.ConnectionError as error:
    print(f"Could not connect to RESTCONF: {error}")
except APIError as error:
    print(f"The API returned an error: {error}")
except ValueError as error:
    print(f"Configuration error: {error}")
