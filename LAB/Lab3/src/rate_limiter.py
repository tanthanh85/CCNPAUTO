"""Rate-control helpers for RESTCONF requests."""

import random
import time


class RateLimiter:
    def __init__(self, requests_per_second):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero")
        self.minimum_gap = 1 / requests_per_second
        self.last_request_time = 0
        self.total_wait = 0

    def wait(self):
        elapsed = time.monotonic() - self.last_request_time
        wait_time = max(0, self.minimum_gap - elapsed)

        if wait_time:
            time.sleep(wait_time)
            self.total_wait += wait_time

        self.last_request_time = time.monotonic()


class BurstRateLimitExperiment:
    """Send a bounded request burst and recover when HTTP 429 is returned."""

    def __init__(self, max_requests, max_seconds, max_backoffs):
        self.max_requests = max_requests
        self.max_seconds = max_seconds
        self.max_backoffs = max_backoffs
        self.request_count = 0
        self.backoff_count = 0

    def run(self, client, path):
        started = time.monotonic()

        while self.request_count < self.max_requests:
            if time.monotonic() - started >= self.max_seconds:
                return "time limit reached"

            response = client.get_response(path)
            self.request_count += 1
            print(f"Request {self.request_count}: HTTP {response.status_code}")

            if response.status_code == 200:
                continue

            if response.status_code == 429:
                if self.backoff_count >= self.max_backoffs:
                    return "backoff limit reached"

                self.backoff_count += 1
                wait_time = self._backoff_seconds(response)
                print(
                    f"Rate limit detected. Backoff {self.backoff_count}/"
                    f"{self.max_backoffs}: waiting {wait_time:.2f} seconds"
                )
                time.sleep(wait_time)
                print("Backoff completed; resuming the RESTCONF request.")
                continue

            client._raise_for_status(response, path)

        return "request limit reached"

    def _backoff_seconds(self, response):
        retry_after = response.headers.get("Retry-After", "").strip()
        if retry_after.isdigit():
            return min(float(retry_after), 60.0)

        exponential = 0.5 * (2 ** (self.backoff_count - 1))
        return min(exponential + random.uniform(0, 0.25), 8.0)
