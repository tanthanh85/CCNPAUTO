#!/usr/bin/env python3
"""Compare normalized interface data collected through CLI and RESTCONF."""

from tabulate import tabulate

from src.iosxe_cli import IOSXECLIClient
from src.iosxe_restconf import IOSXERESTCONFClient, normalize_interfaces
from src.settings import Settings


def main() -> None:
    settings = Settings.from_env()
    with IOSXECLIClient(settings) as device:
        cli_records = device.collect_interfaces()

    restconf_client = IOSXERESTCONFClient(settings)
    restconf_records = normalize_interfaces(restconf_client.get_interfaces_payload())

    cli_by_name = {record["interface"]: record for record in cli_records}
    rest_by_name = {record["interface"]: record for record in restconf_records}
    names = sorted(set(cli_by_name) | set(rest_by_name))

    rows = []
    for name in names:
        cli = cli_by_name.get(name, {})
        rest = rest_by_name.get(name, {})
        cli_state = f"{cli.get('status', '-')}/{cli.get('protocol', '-')}"
        rest_state = f"{rest.get('status', '-')}/{rest.get('protocol', '-')}"
        cli_ip = cli.get("ip_address", "-")
        rest_ip = rest.get("ip_address", "-")
        rows.append(
            [
                name,
                cli_ip,
                rest_ip,
                cli_state,
                rest_state,
                "yes" if cli_ip == rest_ip else "review",
            ]
        )

    print(
        tabulate(
            rows,
            headers=[
                "Interface",
                "CLI IPv4",
                "RESTCONF IPv4",
                "CLI State",
                "RESTCONF State",
                "IP Match",
            ],
            tablefmt="github",
        )
    )


if __name__ == "__main__":
    main()
