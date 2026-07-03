#!/usr/bin/env python3
"""Client for the Lab 3 Flask pagination and rate-limit API."""

import argparse
import csv
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from tabulate import tabulate


class LabAPIClient:
    def __init__(self, base_url, timeout=5, max_retries=4):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.events = []
        self.successful = 0
        self.rate_limited = 0
        self.backoff_resumes = 0

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    def get_page(self, logical_request, page, page_size):
        url = f"{self.base_url}/api/interfaces"

        for attempt in range(1, self.max_retries + 2):
            requested_at = self.utc_now()
            response = self.session.get(
                url,
                params={"page": page, "page_size": page_size},
                timeout=self.timeout,
            )
            responded_at = self.utc_now()
            backoff_seconds = 0.0
            outcome = "success" if response.status_code == 200 else "http_error"

            if response.status_code == 200:
                self.successful += 1
                if attempt > 1:
                    self.backoff_resumes += 1
                    outcome = "resumed_after_backoff"
                self._record(
                    logical_request, attempt, page, response.status_code,
                    requested_at, responded_at, outcome, backoff_seconds,
                )
                return response.json()

            if response.status_code == 429:
                self.rate_limited += 1
                backoff_seconds = self._backoff_seconds(response, attempt)
                self._record(
                    logical_request, attempt, page, response.status_code,
                    requested_at, responded_at, "rate_limited", backoff_seconds,
                )
                if attempt > self.max_retries:
                    raise RuntimeError(
                        f"Logical request {logical_request} exceeded its retry limit"
                    )
                print(
                    f"Request {logical_request}, attempt {attempt}: HTTP 429; "
                    f"backing off for {backoff_seconds:.2f} second(s)"
                )
                time.sleep(backoff_seconds)
                continue

            self._record(
                logical_request, attempt, page, response.status_code,
                requested_at, responded_at, outcome, backoff_seconds,
            )
            response.raise_for_status()

        raise RuntimeError("Request loop ended unexpectedly")

    @staticmethod
    def _backoff_seconds(response, attempt):
        retry_after = response.headers.get("Retry-After", "").strip()
        if retry_after.isdigit():
            return min(float(retry_after), 10.0)
        return min(0.5 * (2 ** (attempt - 1)) + random.uniform(0, 0.25), 8.0)

    def _record(
        self, logical_request, attempt, page, status_code,
        requested_at, responded_at, outcome, backoff_seconds,
    ):
        self.events.append(
            {
                "logical_request": logical_request,
                "attempt": attempt,
                "page": page,
                "requested_at_utc": requested_at,
                "responded_at_utc": responded_at,
                "status_code": status_code,
                "outcome": outcome,
                "backoff_seconds": f"{backoff_seconds:.2f}",
            }
        )

    def write_csv(self, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(self.events[0])
        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.events)


def run_experiment(args):
    client = LabAPIClient(args.base_url)
    sample_page = None

    for logical_request in range(1, args.requests + 1):
        page = ((logical_request - 1) % args.pages) + 1
        payload = client.get_page(logical_request, page, args.page_size)
        if sample_page is None:
            sample_page = payload

    client.write_csv(args.output)
    summary = [
        ["Logical requests", args.requests],
        ["HTTP attempts", len(client.events)],
        ["Successful responses", client.successful],
        ["HTTP 429 responses", client.rate_limited],
        ["Successful resumes after backoff", client.backoff_resumes],
        ["CSV report", args.output],
    ]
    print("\n" + tabulate(summary, headers=["Metric", "Value"], tablefmt="rounded_grid"))
    print("\nFirst successful page metadata:")
    print(sample_page["pagination"])


def run_cache_demo(args):
    url = f"{args.base_url.rstrip('/')}/api/interfaces"
    first = requests.get(url, params={"page": 1, "page_size": 10}, timeout=5)
    first.raise_for_status()
    etag = first.headers.get("ETag")
    print(f"First request: HTTP {first.status_code}, ETag={etag}")

    time.sleep(1.1)
    second = requests.get(
        url,
        params={"page": 1, "page_size": 10},
        headers={"If-None-Match": etag},
        timeout=5,
    )
    print(f"Conditional request: HTTP {second.status_code}")


parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:5000")
parser.add_argument("--requests", type=int, default=100)
parser.add_argument("--pages", type=int, default=10)
parser.add_argument("--page-size", type=int, default=10)
parser.add_argument("--output", default="artifacts/api_results.csv")
parser.add_argument("--cache-demo", action="store_true")
arguments = parser.parse_args()

try:
    if arguments.cache_demo:
        run_cache_demo(arguments)
    else:
        run_experiment(arguments)
except requests.RequestException as error:
    print(f"HTTP request failed: {error}")
except (RuntimeError, ValueError) as error:
    print(f"Experiment stopped: {error}")
