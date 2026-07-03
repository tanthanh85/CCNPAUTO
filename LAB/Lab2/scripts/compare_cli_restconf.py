#!/usr/bin/env python3

from tabulate import tabulate

from src.iosxe_cli import connect, get_interfaces
from src.iosxe_restconf import get_interface_data, normalize_interfaces
from src.settings import load_settings


settings = load_settings()
connection = connect(settings)

try:
    cli_interfaces = get_interfaces(connection)
finally:
    connection.disconnect()

restconf_interfaces = normalize_interfaces(get_interface_data(settings))
cli_by_name = {item["interface"]: item for item in cli_interfaces}
rest_by_name = {item["interface"]: item for item in restconf_interfaces}

rows = []
for name in sorted(set(cli_by_name) | set(rest_by_name)):
    cli = cli_by_name.get(name, {})
    rest = rest_by_name.get(name, {})
    rows.append(
        [
            name,
            cli.get("ip_address", "-"),
            rest.get("ip_address", "-"),
            cli.get("status", "-"),
            rest.get("status", "-"),
        ]
    )

print(tabulate(rows, headers=["Interface", "CLI IP", "RESTCONF IP", "CLI", "RESTCONF"], tablefmt="github"))
