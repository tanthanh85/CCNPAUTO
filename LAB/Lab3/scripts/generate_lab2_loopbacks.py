#!/usr/bin/env python3
"""Generate 100 validated loopback records for the Lab 2 source of truth."""

from __future__ import annotations

import argparse
import ipaddress
from pathlib import Path

import yaml


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--start-id", type=int, default=1001)
    parser.add_argument("--network", default="198.18.0.0/24")
    return parser.parse_args()


def main() -> None:
    try:
        args = arguments()
        if not 1 <= args.count <= 500:
            raise ValueError("count must be between 1 and 500")

        network = ipaddress.ip_network(args.network)
        addresses = list(network.hosts())
        if len(addresses) < args.count:
            raise ValueError(f"{network} has fewer than {args.count} usable addresses")

        loopbacks = []
        for index in range(args.count):
            loopbacks.append(
                {
                    "id": args.start_id + index,
                    "description": f"LAB3_PAGINATION_{index + 1:03d}",
                    "ipv4": str(addresses[index]),
                    "prefix_length": 32,
                    "enabled": True,
                }
            )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        yaml_text = yaml.safe_dump({"loopbacks": loopbacks}, sort_keys=False)
        args.output.write_text(yaml_text)
        print(f"Wrote {len(loopbacks)} loopbacks to {args.output}")

    except (ValueError, OSError) as error:
        print(f"Could not generate the loopback file: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
