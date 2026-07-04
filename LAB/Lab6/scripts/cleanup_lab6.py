#!/usr/bin/env python3

import requests

from src.restconf import RESTCONFClient
from src.settings import Settings


try:
    settings = Settings()
    settings.confirm_changes()
    client = RESTCONFClient(settings)

    for subscription_id in (601, 602, 603):
        status = client.delete_subscription(subscription_id)
        print(f"Subscription {subscription_id}: HTTP {status}")

    status = client.delete_receiver("LAB6_TELEGRAF")
    print(f"Receiver LAB6_TELEGRAF: HTTP {status}")
except PermissionError as error:
    print(f"Safety check stopped cleanup: {error}")
except requests.RequestException as error:
    print(f"RESTCONF transport failed: {error}")
except (RuntimeError, ValueError) as error:
    print(f"Cleanup stopped: {error}")
