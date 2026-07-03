#!/usr/bin/env python3

import argparse

from src.common import (
    INTERFACES_PATH,
    get_json,
    load_settings,
    make_pages,
    make_session,
    normalize_interfaces,
    print_interfaces,
    select_lab_loopbacks,
)


parser = argparse.ArgumentParser()
parser.add_argument("--page-size", type=int, default=20)
parser.add_argument("--no-prompt", action="store_true")
args = parser.parse_args()

settings = load_settings()
session = make_session(settings)
payload = get_json(session, settings, INTERFACES_PATH)
loopbacks = select_lab_loopbacks(normalize_interfaces(payload))
pages = list(make_pages(loopbacks, args.page_size))

print(f"Found {len(loopbacks)} Lab 3 loopbacks in {len(pages)} pages")

for page_number, page in enumerate(pages, start=1):
    print_interfaces(page, f"Page {page_number} of {len(pages)}")
    if page_number < len(pages) and not args.no_prompt:
        input("Press Enter for the next page...")
