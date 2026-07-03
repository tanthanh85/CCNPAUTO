#!/usr/bin/env python3

import argparse
import requests

from src.interface_utils import normalize_interfaces, print_interfaces, select_lab_loopbacks
from src.pagination import Paginator
from src.restconf_client import APIError, INTERFACES_PATH, RESTCONFClient
from src.settings import Settings


parser = argparse.ArgumentParser()
parser.add_argument("--page-size", type=int, default=20)
parser.add_argument("--no-prompt", action="store_true")
args = parser.parse_args()

try:
    client = RESTCONFClient(Settings())
    payload = client.get_json(INTERFACES_PATH)
    loopbacks = select_lab_loopbacks(normalize_interfaces(payload))
    pages = Paginator(loopbacks, args.page_size).pages()

    print(f"Found {len(loopbacks)} Lab 3 loopbacks in {len(pages)} pages")

    for page_number, page in enumerate(pages, start=1):
        print_interfaces(page, f"Page {page_number} of {len(pages)}")
        if page_number < len(pages) and not args.no_prompt:
            input("Press Enter for the next page...")

except requests.Timeout:
    print("The RESTCONF request timed out.")
except requests.ConnectionError as error:
    print(f"Could not connect to RESTCONF: {error}")
except (APIError, ValueError) as error:
    print(f"Pagination failed: {error}")
