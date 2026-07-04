#!/usr/bin/env python3
import logging
import os

from src.common import collect_intent, configure_logging, write_plan

configure_logging("validation.log")
items = collect_intent(os.getenv("NETBOX_DEVICE_NAME", "iosxe-sandbox"))
if not items:
    raise SystemExit("No managed Loopback900-999 interfaces were found in NetBox")
write_plan(items)
logging.info("Validated and froze %s NetBox loopback records", len(items))
for item in items:
    logging.info("Intent %s %s/32", item["name"], item["address"])
