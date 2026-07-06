#!/usr/bin/python
from __future__ import annotations

import random
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import requests
from ansible.module_utils.basic import AnsibleModule

RETRYABLE = {429, 500, 502, 503, 504}


def retry_after_seconds(value):
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
            return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError):
            return None


def run_module():
    module = AnsibleModule(
        argument_spec={
            "url": {"type": "str", "required": True},
            "headers": {"type": "dict", "default": {}, "no_log": True},
            "timeout": {"type": "float", "default": 10.0},
            "max_attempts": {"type": "int", "default": 5},
            "base_delay": {"type": "float", "default": 1.0},
            "max_delay": {"type": "float", "default": 16.0},
            "verify_tls": {"type": "bool", "default": True},
        },
        supports_check_mode=True,
    )
    p = module.params
    history = []

    for attempt in range(1, p["max_attempts"] + 1):
        try:
            response = requests.get(
                p["url"], headers=p["headers"], timeout=p["timeout"],
                verify=p["verify_tls"],
            )
            history.append({"attempt": attempt, "status": response.status_code})
            if response.status_code == 200:
                try:
                    body = response.json()
                except ValueError:
                    module.fail_json(msg="API returned invalid JSON", category="invalid_response", attempts=history)
                module.exit_json(changed=False, json=body, status=response.status_code, attempts=history)

            if response.status_code not in RETRYABLE:
                module.fail_json(
                    msg=f"Unrecoverable HTTP status {response.status_code}",
                    category="unrecoverable_http", status=response.status_code,
                    attempts=history,
                )

            retry_after = retry_after_seconds(response.headers.get("Retry-After"))
        except requests.RequestException as exc:
            history.append({"attempt": attempt, "status": 0, "error": type(exc).__name__})
            retry_after = None

        if attempt == p["max_attempts"]:
            module.fail_json(msg="API retry budget exhausted", category="retry_exhausted", attempts=history)

        exponential = min(p["max_delay"], p["base_delay"] * (2 ** (attempt - 1)))
        delay = retry_after if retry_after is not None else exponential + random.uniform(0, exponential * 0.1)
        time.sleep(delay)


def main():
    run_module()


if __name__ == "__main__":
    main()
