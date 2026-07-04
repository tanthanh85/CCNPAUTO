#!/usr/bin/env python3
import logging
import re

from src.common import configure_logging, connect_device, read_plan

configure_logging("verification.log")
connection = None
try:
    desired = read_plan()
    connection = connect_device()
    output = connection.send_command("show ip interface brief")
    failures = []
    for item in desired:
        pattern = rf"(?m)^\s*{re.escape(item['name'])}\s+{re.escape(item['address'])}\s+YES\s+\S+\s+up\s+up\s*$"
        if not re.search(pattern, output, re.IGNORECASE):
            failures.append(f"{item['name']} {item['address']} is missing or not up/up")
    if failures:
        for failure in failures:
            logging.error(failure)
        raise SystemExit(1)
    logging.info("Verified all %s loopbacks against the frozen plan", len(desired))
finally:
    if connection:
        connection.disconnect()
