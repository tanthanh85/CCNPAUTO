"""A simple rate limiter for RESTCONF requests."""

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
