#!/usr/bin/env python3
import os

import meraki
from dotenv import load_dotenv
from tabulate import tabulate


load_dotenv()
key = os.getenv("MERAKI_DASHBOARD_API_KEY", "")
if not key or key.startswith("REPLACE_WITH_"):
    raise SystemExit("Set MERAKI_DASHBOARD_API_KEY in .env")

dashboard = meraki.DashboardAPI(
    api_key=key, suppress_logging=True, print_console=False,
    wait_on_rate_limit=True, maximum_retries=4,
)
organizations = dashboard.organizations.getOrganizations()
print(tabulate([[o["id"], o["name"]] for o in organizations], headers=["Organization ID", "Name"]))
org_id = os.getenv("MERAKI_ORG_ID") or (organizations[0]["id"] if organizations else None)
if not org_id:
    raise SystemExit("No accessible organization")

networks = dashboard.organizations.getOrganizationNetworks(org_id, total_pages="all")
statuses = dashboard.organizations.getOrganizationDevicesStatuses(org_id, total_pages="all")
print("\nNetworks")
print(tabulate([[n["id"], n["name"], ",".join(n.get("productTypes", []))] for n in networks], headers=["ID", "Name", "Products"]))
print("\nDevice status")
print(tabulate([[d.get("name"), d.get("model"), d.get("serial"), d.get("status"), d.get("networkId")] for d in statuses], headers=["Name", "Model", "Serial", "Status", "Network ID"]))
