"""Simple functions shared by the Lab 3 scripts."""

import os
import re
import time
from urllib.parse import quote

import requests
import urllib3
from dotenv import load_dotenv
from tabulate import tabulate


INTERFACES_PATH = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
INTERFACE_PATH = INTERFACES_PATH + "/interface={}"


def load_settings():
    load_dotenv()

    for name in ["IOSXE_HOST", "IOSXE_USERNAME", "IOSXE_PASSWORD"]:
        value = os.getenv(name, "")
        if not value or value.startswith("REPLACE_WITH_"):
            raise ValueError(f"Set {name} in the .env file")

    return {
        "base_url": f"https://{os.getenv('IOSXE_HOST')}:{os.getenv('IOSXE_HTTPS_PORT', '443')}",
        "username": os.getenv("IOSXE_USERNAME"),
        "password": os.getenv("IOSXE_PASSWORD"),
        "verify_tls": os.getenv("VERIFY_TLS", "false").lower() == "true",
        "rate": float(os.getenv("REQUESTS_PER_SECOND", "5")),
        "connect_timeout": float(os.getenv("IOSXE_CONNECT_TIMEOUT", "10")),
        "read_timeout": float(os.getenv("IOSXE_READ_TIMEOUT", "45")),
        "max_retries": int(os.getenv("IOSXE_MAX_RETRIES", "3")),
    }


def make_session(settings):
    session = requests.Session()
    session.auth = (settings["username"], settings["password"])
    session.headers.update({"Accept": "application/yang-data+json"})
    session.verify = settings["verify_tls"]

    if not settings["verify_tls"]:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return session


def get_json(session, settings, path):
    response = session.get(
        settings["base_url"] + path,
        timeout=(settings["connect_timeout"], settings["read_timeout"]),
    )
    response.raise_for_status()
    return response.json()


def get_interface_json(session, settings, interface_name):
    encoded_name = quote(interface_name, safe="")
    return get_json(session, settings, INTERFACE_PATH.format(encoded_name))


def normalize_interfaces(payload):
    root = payload.get("Cisco-IOS-XE-interfaces-oper:interfaces")
    if root is not None:
        items = root.get("interface", [])
    else:
        items = payload.get("Cisco-IOS-XE-interfaces-oper:interface", [])

    if isinstance(items, dict):
        items = [items]

    interfaces = []
    for item in items:
        admin = str(item.get("admin-status", "unknown")).replace("if-state-", "")
        operational = str(item.get("oper-status", "unknown")).replace(
            "if-oper-state-", ""
        )
        if operational == "ready":
            operational = "up"

        interfaces.append(
            {
                "interface": item.get("name", "-"),
                "ipv4": item.get("ipv4") or "unassigned",
                "admin": admin,
                "operational": operational,
            }
        )

    return interfaces


def select_lab_loopbacks(interfaces):
    selected = []

    for interface in interfaces:
        match = re.fullmatch(r"Loopback(\d+)", interface["interface"])
        if match:
            number = int(match.group(1))
            if 1001 <= number <= 1100:
                selected.append(interface)

    return sorted(selected, key=lambda item: int(item["interface"].replace("Loopback", "")))


def make_pages(items, page_size=20):
    for start in range(0, len(items), page_size):
        yield items[start : start + page_size]


def print_interfaces(interfaces, title):
    rows = []
    for item in interfaces:
        rows.append(
            [item["interface"], item["ipv4"], item["admin"], item["operational"]]
        )

    print(f"\n{title}")
    print(tabulate(rows, headers=["Interface", "IPv4", "Admin", "Operational"], tablefmt="github"))


def wait_for_rate_limit(last_request_time, requests_per_second):
    minimum_gap = 1 / requests_per_second
    elapsed = time.monotonic() - last_request_time
    wait_time = max(0, minimum_gap - elapsed)
    if wait_time:
        time.sleep(wait_time)
    return time.monotonic(), wait_time
