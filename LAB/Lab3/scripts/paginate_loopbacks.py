#!/usr/bin/env python3
"""Retrieve one RESTCONF collection and display 20 loopbacks per page."""

from __future__ import annotations

import argparse

from src.interfaces import INTERFACES_PATH, normalize_interfaces, select_lab_loopbacks
from src.pagination import paginate
from src.reporting import print_interfaces
from src.restconf import BasicRESTCONFClient
from src.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--no-prompt", action="store_true")
    args = parser.parse_args()

    client = BasicRESTCONFClient(Settings.from_env())
    payload = client.get_json(INTERFACES_PATH)
    records = select_lab_loopbacks(normalize_interfaces(payload))
    if len(records) != 100:
        print(f"WARNING: expected 100 Lab 3 loopbacks but found {len(records)}")

    for page in paginate(records, args.page_size):
        print_interfaces(
            list(page.items),
            f"Loopbacks page {page.number}/{page.total_pages} "
            f"({page.total_items} total)",
        )
        if page.has_next and not args.no_prompt:
            input("Press Enter for the next page...")


if __name__ == "__main__":
    main()
