"""A thread-safe request pacer that prevents client-generated bursts."""

from __future__ import annotations

import threading
import time


class RequestPacer:
    def __init__(self, requests_per_second: float) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero")
        self.minimum_interval = 1.0 / requests_per_second
        self._next_request = 0.0
        self._lock = threading.Lock()
        self.total_wait_seconds = 0.0

    def wait(self) -> float:
        """Wait until the next evenly spaced request slot and return delay."""
        with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next_request - now)
            if delay:
                time.sleep(delay)
                self.total_wait_seconds += delay
            sent_at = time.monotonic()
            self._next_request = max(self._next_request, sent_at) + self.minimum_interval
            return delay
