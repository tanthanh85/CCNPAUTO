#!/usr/bin/env python3

import requests
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from tabulate import tabulate

from src.iosxe_cli import IOSXEDevice
from src.iosxe_restconf import RESTCONFClient
from src.settings import Settings


device = None

try:
    settings = Settings()

    device = IOSXEDevice(settings)
    device.connect()
    cli_interfaces = device.get_interfaces()

    restconf = RESTCONFClient(settings)
    rest_interfaces = restconf.normalize(restconf.get_interfaces())

    cli_by_name = {item["interface"]: item for item in cli_interfaces}
    rest_by_name = {item["interface"]: item for item in rest_interfaces}
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

    print(
        tabulate(
            rows,
            headers=["Interface", "CLI IP", "RESTCONF IP", "CLI", "RESTCONF"],
            tablefmt="github",
        )
    )

except (NetmikoAuthenticationException, NetmikoTimeoutException) as error:
    print(f"CLI collection failed: {error}")
except requests.RequestException as error:
    print(f"RESTCONF collection failed: {error}")
except (ValueError, RuntimeError) as error:
    print(f"Comparison failed: {error}")
finally:
    if device:
        device.disconnect()
