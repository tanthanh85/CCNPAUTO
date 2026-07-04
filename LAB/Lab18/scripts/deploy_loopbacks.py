#!/usr/bin/env python3
import logging

from src.common import configure_logging, connect_device, read_plan

configure_logging("deployment.log")
connection = None
try:
    desired = read_plan()
    connection = connect_device()
    commands = []
    for item in desired:
        commands.extend(
            [
                f"interface {item['name']}",
                f"description {item['description']}",
                f"ip address {item['address']} {item['netmask']}",
                "no shutdown",
            ]
        )
    logging.info("Connected to reserved IOS XE target")
    response = connection.send_config_set(commands)
    logging.info("Submitted %s NetBox-managed loopbacks", len(desired))
    logging.info("Device response:\n%s", response)
finally:
    if connection:
        connection.disconnect()
