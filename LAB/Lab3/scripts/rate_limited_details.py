#!/usr/bin/env python3

import requests

from src.rate_limiter import BurstRateLimitExperiment
from src.restconf_client import APIError, INTERFACES_PATH, RESTCONFClient
from src.settings import Settings


try:
    settings = Settings()
    client = RESTCONFClient(settings)
    experiment = BurstRateLimitExperiment(
        settings.burst_max_requests,
        settings.burst_max_seconds,
        settings.burst_max_backoffs,
    )

    print("Starting a bounded high-frequency RESTCONF experiment.")
    print(
        f"Safety limits: {settings.burst_max_requests} requests, "
        f"{settings.burst_max_seconds:.0f} seconds, "
        f"{settings.burst_max_backoffs} backoffs"
    )
    result = experiment.run(client, INTERFACES_PATH)

    print(f"\nExperiment stopped: {result}")
    print(f"Requests sent: {experiment.request_count}")
    print(f"HTTP 429 backoffs: {experiment.backoff_count}")

    if experiment.backoff_count == 0:
        print("IOS XE did not return HTTP 429 within the safety limits.")

except requests.Timeout:
    print("A RESTCONF request timed out.")
except requests.ConnectionError as error:
    print(f"Could not connect to RESTCONF: {error}")
except APIError as error:
    print(f"The API returned an error: {error}")
except ValueError as error:
    print(f"Configuration error: {error}")
