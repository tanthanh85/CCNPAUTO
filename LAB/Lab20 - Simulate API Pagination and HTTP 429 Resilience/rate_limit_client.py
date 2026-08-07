"""Send 100 logical requests and recover from HTTP 429 responses."""

from __future__ import annotations

import csv
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
API_URL = "http://127.0.0.1:5000/api/limited/interfaces?page=1&per_page=20"
REQUEST_COUNT = 100
MAX_ATTEMPTS = 5
TIMEOUT_SECONDS = 5


def configure_logging() -> Path:
    """Create timestamped diagnostic and CSV evidence files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_dir = PROJECT_ROOT / "logs"
    result_dir = PROJECT_ROOT / "results"
    log_dir.mkdir(exist_ok=True)
    result_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(
                log_dir / f"rate_limit_client_{timestamp}.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )
    return result_dir / f"rate_limit_results_{timestamp}.csv"


def retry_after_seconds(header_value: str | None, attempt: int) -> float:
    """Use Retry-After when valid; otherwise use bounded exponential backoff."""
    if header_value:
        try:
            return max(0.0, float(header_value))
        except ValueError:
            try:
                retry_time = parsedate_to_datetime(header_value)
                seconds = retry_time.timestamp() - time.time()
                return max(0.0, seconds)
            except (TypeError, ValueError, OverflowError):
                pass

    exponential = min(8.0, 0.5 * (2 ** (attempt - 1)))
    return exponential + random.uniform(0.0, 0.25)


@dataclass
class RunStatistics:
    successful_requests: int = 0
    rate_limited_responses: int = 0
    recovered_requests: int = 0
    failed_requests: int = 0


class ResilientApiClient:
    """HTTP client with explicit flow control for 429 responses."""

    def __init__(self, api_url: str, csv_path: Path) -> None:
        self.api_url = api_url
        self.csv_path = csv_path
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.statistics = RunStatistics()

    def record_attempt(
        self,
        writer: csv.DictWriter,
        logical_request: int,
        attempt: int,
        status_code: int | str,
        outcome: str,
        retry_after: str,
        wait_seconds: float,
        elapsed_ms: float,
    ) -> None:
        """Write one row for every network attempt, including retries."""
        writer.writerow(
            {
                "timestamp": datetime.now().astimezone().isoformat(
                    timespec="milliseconds"
                ),
                "logical_request": logical_request,
                "attempt": attempt,
                "http_status": status_code,
                "outcome": outcome,
                "retry_after": retry_after,
                "wait_seconds": f"{wait_seconds:.3f}",
                "elapsed_ms": f"{elapsed_ms:.3f}",
            }
        )

    def run(self, request_count: int) -> RunStatistics:
        """Execute logical requests while tracking 429 recovery."""
        fieldnames = [
            "timestamp",
            "logical_request",
            "attempt",
            "http_status",
            "outcome",
            "retry_after",
            "wait_seconds",
            "elapsed_ms",
        ]
        with self.csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for logical_request in range(1, request_count + 1):
                encountered_429 = False

                for attempt in range(1, MAX_ATTEMPTS + 1):
                    started = time.perf_counter()
                    try:
                        response = self.session.get(
                            self.api_url,
                            timeout=TIMEOUT_SECONDS,
                        )
                    except requests.RequestException as exc:
                        elapsed_ms = (time.perf_counter() - started) * 1000
                        self.record_attempt(
                            writer,
                            logical_request,
                            attempt,
                            "network_error",
                            type(exc).__name__,
                            "",
                            0.0,
                            elapsed_ms,
                        )
                        self.logger.error(
                            "Request failed logical_request=%d attempt=%d error=%s",
                            logical_request,
                            attempt,
                            exc,
                        )
                        self.statistics.failed_requests += 1
                        break

                    elapsed_ms = (time.perf_counter() - started) * 1000
                    if response.status_code == 200:
                        response.json()
                        outcome = "recovered_success" if encountered_429 else "success"
                        self.record_attempt(
                            writer,
                            logical_request,
                            attempt,
                            200,
                            outcome,
                            "",
                            0.0,
                            elapsed_ms,
                        )
                        self.statistics.successful_requests += 1
                        if encountered_429:
                            self.statistics.recovered_requests += 1
                        break

                    if response.status_code == 429:
                        encountered_429 = True
                        self.statistics.rate_limited_responses += 1
                        retry_after = response.headers.get("Retry-After")
                        wait_seconds = retry_after_seconds(retry_after, attempt)
                        self.record_attempt(
                            writer,
                            logical_request,
                            attempt,
                            429,
                            "rate_limited",
                            retry_after or "",
                            wait_seconds,
                            elapsed_ms,
                        )
                        self.logger.warning(
                            "Rate limited logical_request=%d attempt=%d "
                            "wait_seconds=%.3f",
                            logical_request,
                            attempt,
                            wait_seconds,
                        )
                        if attempt < MAX_ATTEMPTS:
                            time.sleep(wait_seconds)
                            continue

                    else:
                        self.record_attempt(
                            writer,
                            logical_request,
                            attempt,
                            response.status_code,
                            "unrecoverable_http_error",
                            "",
                            0.0,
                            elapsed_ms,
                        )
                        self.logger.error(
                            "Unrecoverable HTTP response logical_request=%d "
                            "status=%d",
                            logical_request,
                            response.status_code,
                        )

                    self.statistics.failed_requests += 1
                    break

        return self.statistics


def main() -> None:
    csv_path = configure_logging()
    client = ResilientApiClient(API_URL, csv_path)
    statistics = client.run(REQUEST_COUNT)

    print("\nHTTP resilience run summary")
    print(f"Logical requests requested : {REQUEST_COUNT}")
    print(f"Successful requests        : {statistics.successful_requests}")
    print(f"HTTP 429 responses         : {statistics.rate_limited_responses}")
    print(f"Recovered after backoff    : {statistics.recovered_requests}")
    print(f"Failed logical requests    : {statistics.failed_requests}")
    print(f"CSV evidence               : {csv_path}")


if __name__ == "__main__":
    main()

