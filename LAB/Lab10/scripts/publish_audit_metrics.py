from __future__ import annotations

import glob
import json
import os
import sys

import requests


def safe_tag(value):
    return str(value).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def main():
    url = os.environ["INFLUX_URL"].rstrip("/")
    org, bucket, token = (os.environ[k] for k in ("INFLUX_ORG", "INFLUX_BUCKET", "INFLUX_TOKEN"))
    lines = []
    for path in glob.glob("artifacts/*.jsonl"):
        with open(path, encoding="utf-8") as stream:
            for raw in stream:
                event = json.loads(raw)
                if event.get("event") != "task_result":
                    continue
                tags = ",".join(
                    f"{k}={safe_tag(event.get(k, 'unknown'))}"
                    for k in ("pipeline_id", "job_name", "host", "status")
                )
                changed = "true" if event.get("changed") else "false"
                lines.append(f"automation_task,{tags} duration_seconds={float(event.get('duration_seconds', 0))},changed={changed}")
    if not lines:
        print("No task events found; nothing to publish")
        return 0
    response = requests.post(
        f"{url}/api/v2/write", params={"org": org, "bucket": bucket, "precision": "ns"},
        headers={"Authorization": f"Token {token}", "Content-Type": "text/plain"},
        data="\n".join(lines), timeout=10,
    )
    response.raise_for_status()
    print(f"Published {len(lines)} task metrics to InfluxDB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
