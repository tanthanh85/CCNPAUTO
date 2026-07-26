#!/usr/bin/python
from __future__ import annotations

import logging
import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
from ansible.module_utils.basic import AnsibleModule

RETRYABLE = {429, 500, 502, 503, 504}


def configure_module_logging(enabled, level, log_dir):
    logger = logging.getLogger("resilient_http")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    if not enabled:
        logger.addHandler(logging.NullHandler())
        return logger, None

    destination = Path(log_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    path = destination / f"resilient_http_{timestamp}_{os.getpid()}.log"
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(getattr(logging, str(level).upper(), logging.DEBUG))
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    logger.addHandler(handler)
    logger.info("Resilient HTTP module logging initialized log_file=%s", path)
    return logger, path


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
            "enable_file_logging": {"type": "bool", "default": False},
            "log_level": {
                "type": "str",
                "default": "DEBUG",
                "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            },
            "log_dir": {"type": "path", "default": "logs"},
        },
        supports_check_mode=True,
    )
    p = module.params
    history = []
    logger, log_path = configure_module_logging(
        p["enable_file_logging"],
        p["log_level"],
        p["log_dir"],
    )
    logger.info(
        "Starting resilient GET url=%s timeout=%s max_attempts=%s "
        "base_delay=%s max_delay=%s verify_tls=%s check_mode=%s",
        p["url"],
        p["timeout"],
        p["max_attempts"],
        p["base_delay"],
        p["max_delay"],
        p["verify_tls"],
        module.check_mode,
    )

    for attempt in range(1, p["max_attempts"] + 1):
        logger.debug("Starting request attempt=%d", attempt)
        started = time.perf_counter()
        try:
            response = requests.get(
                p["url"], headers=p["headers"], timeout=p["timeout"],
                verify=p["verify_tls"],
            )
            history.append({"attempt": attempt, "status": response.status_code})
            logger.info(
                "Received HTTP response attempt=%d status=%d "
                "elapsed_seconds=%.3f",
                attempt,
                response.status_code,
                time.perf_counter() - started,
            )
            if response.status_code == 200:
                try:
                    body = response.json()
                except ValueError:
                    logger.exception("HTTP 200 response contained invalid JSON")
                    module.fail_json(
                        msg="API returned invalid JSON",
                        category="invalid_response",
                        attempts=history,
                        diagnostic_log=str(log_path) if log_path else None,
                    )
                logger.info(
                    "Request succeeded attempts=%d json_type=%s",
                    attempt,
                    type(body).__name__,
                )
                module.exit_json(
                    changed=False,
                    json=body,
                    status=response.status_code,
                    attempts=history,
                    diagnostic_log=str(log_path) if log_path else None,
                )

            if response.status_code not in RETRYABLE:
                logger.error(
                    "Unrecoverable HTTP status=%d attempt=%d",
                    response.status_code,
                    attempt,
                )
                module.fail_json(
                    msg=f"Unrecoverable HTTP status {response.status_code}",
                    category="unrecoverable_http", status=response.status_code,
                    attempts=history,
                    diagnostic_log=str(log_path) if log_path else None,
                )

            retry_after = retry_after_seconds(response.headers.get("Retry-After"))
            logger.warning(
                "Retryable HTTP status=%d attempt=%d retry_after=%s",
                response.status_code,
                attempt,
                retry_after,
            )
        except requests.RequestException as exc:
            history.append({"attempt": attempt, "status": 0, "error": type(exc).__name__})
            logger.warning(
                "Transport failure attempt=%d error_type=%s "
                "elapsed_seconds=%.3f",
                attempt,
                type(exc).__name__,
                time.perf_counter() - started,
                exc_info=True,
            )
            retry_after = None

        if attempt == p["max_attempts"]:
            logger.error("API retry budget exhausted history=%s", history)
            module.fail_json(
                msg="API retry budget exhausted",
                category="retry_exhausted",
                attempts=history,
                diagnostic_log=str(log_path) if log_path else None,
            )

        exponential = min(p["max_delay"], p["base_delay"] * (2 ** (attempt - 1)))
        delay = retry_after if retry_after is not None else exponential + random.uniform(0, exponential * 0.1)
        logger.info(
            "Waiting before retry attempt=%d delay_seconds=%.3f source=%s",
            attempt + 1,
            delay,
            "Retry-After" if retry_after is not None else "exponential_backoff_with_jitter",
        )
        time.sleep(delay)


def main():
    run_module()


if __name__ == "__main__":
    main()
