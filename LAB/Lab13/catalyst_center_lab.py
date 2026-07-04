#!/usr/bin/env python3
import os
import time

import requests
import urllib3
from dotenv import load_dotenv
from tabulate import tabulate


class CatalystCenterClient:
    def __init__(self, url, username, password, verify):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = verify
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def authenticate(self):
        response = self.session.post(
            self.url + "/dna/system/api/v1/auth/token",
            auth=(self.username, self.password), timeout=30,
        )
        response.raise_for_status()
        self.session.headers["X-Auth-Token"] = response.json()["Token"]

    def get(self, path, params=None):
        response = self.session.get(self.url + path, params=params, timeout=60)
        if response.status_code == 429:
            time.sleep(min(int(response.headers.get("Retry-After", "1")), 30))
            response = self.session.get(self.url + path, params=params, timeout=60)
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
        return response.json().get("response", response.json())


load_dotenv()
required = ["CATALYST_CENTER_URL", "CATALYST_CENTER_USERNAME", "CATALYST_CENTER_PASSWORD"]
if any(not os.getenv(name) or os.getenv(name).startswith("REPLACE_WITH_") for name in required):
    raise SystemExit("Complete the Catalyst Center settings in .env")

client = CatalystCenterClient(
    os.environ["CATALYST_CENTER_URL"], os.environ["CATALYST_CENTER_USERNAME"],
    os.environ["CATALYST_CENTER_PASSWORD"], os.getenv("VERIFY_TLS", "false").lower() == "true",
)
client.authenticate()
devices = client.get("/dna/intent/api/v1/network-device")
print(tabulate([[d.get("hostname"), d.get("platformId"), d.get("managementIpAddress"), d.get("reachabilityStatus")] for d in devices], headers=["Hostname", "Platform", "Management IP", "Reachability"]))

now_ms = int(time.time() * 1000)
for title, path in [("Network health", "/dna/intent/api/v1/network-health"), ("Client health", "/dna/intent/api/v1/client-health")]:
    try:
        result = client.get(path, params={"timestamp": now_ms})
        print(f"\n{title}: {result}")
    except RuntimeError as error:
        print(f"\n{title} unavailable on this release or dataset: {error}")
