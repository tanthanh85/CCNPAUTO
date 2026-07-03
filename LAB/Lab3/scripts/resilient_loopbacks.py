#!/usr/bin/env python3

import argparse

from src.interface_utils import normalize_interfaces, print_interfaces, select_lab_loopbacks
from src.pagination import Paginator
from src.rate_limiter import RateLimiter
from src.restconf_client import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    INTERFACES_PATH,
    NotFoundError,
    ResilientRESTCONFClient,
)
from src.settings import Settings


parser = argparse.ArgumentParser()
parser.add_argument("--demo-not-found", action="store_true")
args = parser.parse_args()

try:
    settings = Settings()
    client = ResilientRESTCONFClient(settings)
    limiter = RateLimiter(settings.requests_per_second)

    if args.demo_not_found:
        try:
            client.get_interface("Loopback999999")
        except NotFoundError as error:
            print(f"Controlled 404: {error}")
            print("This item will not be retried. Collection will continue.\n")

    index = client.get_json(INTERFACES_PATH)
    loopbacks = select_lab_loopbacks(normalize_interfaces(index))
    pages = Paginator(loopbacks, 20).pages()
    collected = []

    for page_number, page in enumerate(pages, start=1):
        page_details = []

        for loopback in page:
            limiter.wait()

            try:
                detail = client.get_interface(loopback["interface"])
                page_details.extend(normalize_interfaces(detail))
            except NotFoundError:
                print(f"Skipping {loopback['interface']}; it no longer exists")

        collected.extend(page_details)
        print_interfaces(page_details, f"Resilient page {page_number}")

    print(f"\nCollected: {len(collected)}")
    print(f"HTTP attempts: {client.attempts}")
    print(f"Retries: {client.retries}")
    print(f"Status codes: {client.status_codes}")
    print(f"Rate-limit waiting: {limiter.total_wait:.2f} seconds")

except AuthenticationError:
    print("Authentication failed. Correct the credentials; do not retry them.")
except AuthorizationError:
    print("The account is not authorized for this RESTCONF resource.")
except APIError as error:
    print(f"Collection stopped after controlled error handling: {error}")
except ValueError as error:
    print(f"Configuration error: {error}")
