#!/usr/bin/env python3
import logging
import re

from src.common import configure_logging, connect, load_vlans

configure_logging("verification.log")
connection = None
try:
    expected = load_vlans()
    connection = connect()
    output = connection.send_command("show vlan brief")
    failures = []
    for vlan in expected:
        pattern = rf"(?m)^\s*{vlan['id']}\s+{re.escape(vlan['name'])}\s+"
        if not re.search(pattern, output):
            failures.append(f"VLAN {vlan['id']} {vlan['name']} is missing or incorrect")
    if failures:
        for failure in failures:
            logging.error(failure)
        raise SystemExit(1)
    logging.info("Verified all %s VLAN records", len(expected))
finally:
    if connection:
        connection.disconnect()
