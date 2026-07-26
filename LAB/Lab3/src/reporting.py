"""Print CLI and RESTCONF data as simple tables."""

import logging

from tabulate import tabulate


logger = logging.getLogger(__name__)


def print_version(records):
    logger.debug("Formatting version report records=%d", len(records))
    rows = []

    for item in records:
        serial = item.get("serial", "-")
        if isinstance(serial, list):
            serial = ", ".join(serial)

        rows.append(
            [
                item.get("hostname", "-"),
                item.get("version", "-"),
                item.get("running_image", "-"),
                item.get("uptime", "-"),
                serial,
            ]
        )

    print("\nIOS XE Software and Platform")
    print(
        tabulate(
            rows,
            headers=["Hostname", "Version", "Image", "Uptime", "Serial"],
            tablefmt="github",
        )
    )


def print_interfaces(records, title):
    logger.debug("Formatting interface report title=%s records=%d", title, len(records))
    rows = []

    for item in records:
        rows.append(
            [
                item.get("interface", "-"),
                item.get("ip_address", "unassigned"),
                item.get("status", "unknown"),
                item.get("protocol", "unknown"),
            ]
        )

    print(f"\n{title}")
    print(
        tabulate(
            rows,
            headers=["Interface", "IPv4 Address", "Admin Status", "Protocol"],
            tablefmt="github",
        )
    )
