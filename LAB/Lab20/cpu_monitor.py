#!/usr/bin/env python3
"""Sample IOS XE CPU utilization once per minute from Guest Shell."""

from __future__ import annotations

import argparse
import csv
import re
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CSV = Path("/bootflash/guest-share/lab20/cpu_usage.csv")
CPU_COMMAND = "show processes cpu | include CPU utilization"
CPU_PATTERN = re.compile(
    r"five seconds:\s*(?P<five>\d+(?:\.\d+)?)%"
    r"(?:/(?P<interrupt>\d+(?:\.\d+)?)%)?;\s*"
    r"one minute:\s*(?P<one>\d+(?:\.\d+)?)%;\s*"
    r"five minutes:\s*(?P<five_min>\d+(?:\.\d+)?)%",
    re.IGNORECASE,
)


class CPUMonitorError(RuntimeError):
    """Represent a controlled collection or parsing failure."""


def parse_cpu_output(output: str) -> dict[str, float]:
    """Extract IOS XE CPU percentages from `show processes cpu`."""
    match = CPU_PATTERN.search(output)
    if not match:
        raise CPUMonitorError(f"Unrecognized IOS XE CPU output: {output.strip()!r}")
    return {
        "cpu_5_seconds_pct": float(match.group("five")),
        "cpu_interrupt_5_seconds_pct": float(match.group("interrupt") or 0),
        "cpu_1_minute_pct": float(match.group("one")),
        "cpu_5_minutes_pct": float(match.group("five_min")),
    }


def collect_cpu() -> dict[str, float]:
    """Execute a read-only IOS XE command through the Guest Shell bridge."""
    try:
        result = subprocess.run(
            ["dohost", CPU_COMMAND],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CPUMonitorError("The dohost command is unavailable; run inside IOS XE Guest Shell") from exc
    except subprocess.TimeoutExpired as exc:
        raise CPUMonitorError("IOS XE CPU command timed out after 20 seconds") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise CPUMonitorError(f"dohost failed with exit code {result.returncode}: {detail}")
    return parse_cpu_output(result.stdout)


def append_sample(csv_path: Path, sample: dict[str, float]) -> None:
    """Append one durable CSV row and create the header when necessary."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not csv_path.exists() or csv_path.stat().st_size == 0
    row = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **sample}
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=row.keys())
        if new_file:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()


def run(csv_path: Path, interval: int, count: int | None) -> int:
    """Collect immediately, then repeat on a monotonic one-minute schedule."""
    stopping = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    completed = 0
    next_run = time.monotonic()
    while not stopping and (count is None or completed < count):
        try:
            sample = collect_cpu()
            append_sample(csv_path, sample)
            completed += 1
            print(f"Recorded sample {completed}: {sample}", flush=True)
        except CPUMonitorError as exc:
            print(f"Collection error: {exc}", flush=True)

        next_run += interval
        while not stopping:
            remaining = next_run - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 1))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--interval", type=int, default=60, help="seconds between samples")
    parser.add_argument("--count", type=int, help="stop after this many successful samples")
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("--interval must be at least 1 second")
    if args.count is not None and args.count < 1:
        parser.error("--count must be at least 1")
    return run(args.csv, args.interval, args.count)


if __name__ == "__main__":
    raise SystemExit(main())

