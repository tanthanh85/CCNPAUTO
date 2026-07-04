#!/usr/bin/env python3
"""Summarize structured application or audit logs."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("path", nargs="?", default="logs/application.jsonl")
arguments = parser.parse_args()

levels = Counter()
events = Counter()
outcomes = Counter()
correlations = defaultdict(list)

for line_number, line in enumerate(Path(arguments.path).read_text(encoding="utf-8").splitlines(), 1):
    try:
        event = json.loads(line)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON on line {line_number}: {error}")
    levels[event.get("level", "UNKNOWN")] += 1
    events[event.get("event_type", "unspecified")] += 1
    if event.get("outcome"):
        outcomes[event["outcome"]] += 1
    correlations[event.get("correlation_id", "none")].append(event)

print("Levels:", dict(levels))
print("Events:", dict(events))
print("Outcomes:", dict(outcomes))
print("Correlation IDs:", len(correlations))

for correlation_id, records in correlations.items():
    print(f"\n{correlation_id}: {len(records)} events")
    for event in records:
        device = event.get("device", "-")
        print(f"  {event['timestamp']} {event['level']:<7} {device:<12} {event.get('event_type', '-')}")
