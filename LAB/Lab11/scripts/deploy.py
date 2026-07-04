#!/usr/bin/env python3
import logging

from src.common import configure_logging, connect, load_vlans

configure_logging("deployment.log")
connection = None
try:
    vlans = load_vlans()
    commands = []
    for vlan in vlans:
        commands.extend([f"vlan {vlan['id']}", f"name {vlan['name']}"])
    connection = connect()
    logging.info("Connected to the Catalyst 9000v target")
    result = connection.send_config_set(commands)
    logging.info("Applied %s VLAN records", len(vlans))
    logging.info("Device response:\n%s", result)
finally:
    if connection:
        connection.disconnect()
