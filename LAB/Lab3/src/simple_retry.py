"""A small GET retry loop used by the final Lab 3 task."""

import random
import time

import requests


def get_json_with_retry(session, settings, path, statistics):
    attempts_allowed = settings["max_retries"] + 1

    for attempt in range(1, attempts_allowed + 1):
        statistics["attempts"] += 1

        try:
            response = session.get(
                settings["base_url"] + path,
                timeout=(settings["connect_timeout"], settings["read_timeout"]),
            )
        except (requests.Timeout, requests.ConnectionError) as error:
            print(f"Connection problem on attempt {attempt}: {error}")
            if attempt == attempts_allowed:
                return None, "failed"
            statistics["retries"] += 1
            time.sleep(0.5 * (2 ** (attempt - 1)) + random.uniform(0, 0.25))
            continue

        status = response.status_code
        statistics["status_codes"][status] = statistics["status_codes"].get(status, 0) + 1

        if status == 200:
            try:
                return response.json(), "ok"
            except requests.JSONDecodeError:
                print("The server returned HTTP 200, but the body was not valid JSON")
                return None, "failed"

        if status in [401, 403]:
            print(f"HTTP {status}: correct credentials or permissions; do not retry")
            return None, "fatal"

        if status == 404:
            print(f"HTTP 404: resource not found: {path}")
            return None, "not_found"

        if status == 429 or status >= 500:
            if attempt == attempts_allowed:
                print(f"HTTP {status}: retry limit reached")
                return None, "failed"

            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                wait_time = min(int(retry_after), 60)
            else:
                wait_time = 0.5 * (2 ** (attempt - 1)) + random.uniform(0, 0.25)

            statistics["retries"] += 1
            print(f"HTTP {status}: waiting {wait_time:.2f} seconds before retry")
            time.sleep(wait_time)
            continue

        print(f"HTTP {status}: request failed and will not be retried")
        return None, "failed"

    return None, "failed"
