"""Retrieve every record by following pagination links returned by the API."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:5000"
TIMEOUT_SECONDS = 5


def configure_logging() -> None:
    """Create a unique client log for this execution."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(
                log_dir / f"pagination_client_{timestamp}.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


class PaginatedApiClient:
    """Small client that follows server-provided next links."""

    def __init__(self, base_url: str) -> None:
        self.session = requests.Session()
        self.first_url = f"{base_url}/api/interfaces?page=1&per_page=20"
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def validate_page(payload: Any) -> None:
        """Reject malformed responses before the client trusts them."""
        if not isinstance(payload, dict):
            raise ValueError("Response body must be a JSON object.")
        if not isinstance(payload.get("data"), list):
            raise ValueError("Response must contain a data list.")
        if not isinstance(payload.get("links"), dict):
            raise ValueError("Response must contain a links object.")
        if "next" not in payload["links"]:
            raise ValueError("Response links must contain the next key.")

    def retrieve_all(self) -> list[dict[str, object]]:
        """Follow next links until the server returns null."""
        records: list[dict[str, object]] = []
        visited_urls: set[str] = set()
        next_url: str | None = self.first_url

        while next_url:
            if next_url in visited_urls:
                raise RuntimeError(f"Pagination loop detected at {next_url}")
            visited_urls.add(next_url)

            self.logger.info("Requesting page url=%s", next_url)
            response = self.session.get(next_url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            self.validate_page(payload)

            page_records = payload["data"]
            records.extend(page_records)
            page_number = payload.get("pagination", {}).get("page", "unknown")
            self.logger.info(
                "Accepted page=%s records=%d cumulative_records=%d",
                page_number,
                len(page_records),
                len(records),
            )
            next_url = payload["links"]["next"]

        return records


def display_records(records: list[dict[str, object]]) -> None:
    """Print a compact table so the learner can verify the result."""
    print(f"{'ID':>3}  {'Interface':<14} {'IPv4':<19} {'Status':<6}")
    print("-" * 49)
    for record in records:
        print(
            f"{record['id']:>3}  {record['name']:<14} "
            f"{record['ipv4']:<19} {record['status']:<6}"
        )
    print(f"\nRetrieved {len(records)} interfaces across all pages.")


def main() -> None:
    configure_logging()
    client = PaginatedApiClient(BASE_URL)
    try:
        records = client.retrieve_all()
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        logging.getLogger(__name__).exception(
            "Pagination collection failed error=%s", exc
        )
        raise SystemExit(1) from exc
    display_records(records)


if __name__ == "__main__":
    main()

