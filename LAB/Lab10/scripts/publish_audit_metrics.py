from __future__ import annotations

import glob
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
import urllib3

from src.logging_config import configure_logging


logger = logging.getLogger(__name__)


def safe_tag(value):
    return str(value).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def main():
    configure_logging("publish_audit_metrics", project_root=Path.cwd())
    logger.info("Starting audit-to-InfluxDB metric publication")
    url = os.environ["INFLUX_URL"].rstrip("/")
    org, bucket, token = (os.environ[k] for k in ("INFLUX_ORG", "INFLUX_BUCKET", "INFLUX_TOKEN"))
    lines = []
    paths = sorted(glob.glob("artifacts/*.jsonl"))
    logger.info(
        "Discovered %d JSONL audit artifact(s) destination=%s "
        "organization=%s bucket=%s token_configured=%s",
        len(paths),
        url,
        org,
        bucket,
        bool(token),
    )
    for path in paths:
        file_events = 0
        with open(path, encoding="utf-8") as stream:
            for line_number, raw in enumerate(stream, start=1):
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    logger.exception(
                        "Invalid JSONL event path=%s line=%d",
                        path,
                        line_number,
                    )
                    raise
                if event.get("event") != "task_result":
                    continue
                file_events += 1
                tags = ",".join(
                    f"{k}={safe_tag(event.get(k, 'unknown'))}"
                    for k in ("pipeline_id", "job_name", "host", "status")
                )
                changed = "true" if event.get("changed") else "false"
                lines.append(f"automation_task,{tags} duration_seconds={float(event.get('duration_seconds', 0))},changed={changed}")
        logger.info("Converted audit artifact path=%s task_events=%d", path, file_events)
    if not lines:
        logger.warning("No task_result events found; no metrics will be published")
        print("No task events found; nothing to publish")
        return 0
    logger.info("Publishing %d line-protocol metric(s)", len(lines))
    started = time.perf_counter()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(
        f"{url}/api/v2/write", params={"org": org, "bucket": bucket, "precision": "ns"},
        headers={"Authorization": f"Token {token}", "Content-Type": "text/plain"},
        data="\n".join(lines), timeout=10, verify=False,
    )
    logger.info(
        "InfluxDB response status=%d elapsed_seconds=%.3f",
        response.status_code,
        time.perf_counter() - started,
    )
    response.raise_for_status()
    logger.info("Published %d task metric(s) successfully", len(lines))
    print(f"Published {len(lines)} task metrics to InfluxDB")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, ValueError, requests.RequestException):
        logger.exception("Audit metric publication failed")
        raise
