#!/usr/bin/env python3
import os
import time

import requests
from dotenv import load_dotenv
from tabulate import tabulate


class WebexClient:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})
        self.base = "https://webexapis.com/v1"

    def request(self, method, path, **kwargs):
        for attempt in range(1, 5):
            response = self.session.request(method, self.base + path, timeout=30, **kwargs)
            if response.status_code != 429:
                if response.status_code >= 400:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                return response
            delay = int(response.headers.get("Retry-After", attempt))
            time.sleep(min(delay, 30))
        raise RuntimeError("Webex rate limit retry budget exhausted")

    def me(self):
        return self.request("GET", "/people/me").json()

    def rooms(self):
        return self.request("GET", "/rooms", params={"max": 50}).json().get("items", [])

    def create_room(self, title):
        return self.request("POST", "/rooms", json={"title": title}).json()

    def post_message(self, room_id, markdown):
        return self.request("POST", "/messages", json={"roomId": room_id, "markdown": markdown}).json()

    def messages(self, room_id):
        return self.request("GET", "/messages", params={"roomId": room_id, "max": 20}).json().get("items", [])

    def delete_room(self, room_id):
        return self.request("DELETE", f"/rooms/{room_id}")


load_dotenv()
token = os.getenv("WEBEX_ACCESS_TOKEN", "")
if not token or token.startswith("REPLACE_WITH_"):
    raise SystemExit("Set WEBEX_ACCESS_TOKEN in .env")

client = WebexClient(token)
identity = client.me()
emails = identity.get("emails") or [""]
print(f"Authenticated as: {identity.get('displayName')} ({emails[0]})")
rooms = client.rooms()
print(tabulate([[r.get("title"), r.get("type"), r.get("id")[:12] + "..."] for r in rooms], headers=["Title", "Type", "ID"]))

if os.getenv("ALLOW_WEBEX_CHANGES", "false").lower() != "true":
    print("Read-only run complete. Set ALLOW_WEBEX_CHANGES=true for the room/message task.")
    raise SystemExit(0)

title = os.getenv("WEBEX_ROOM_TITLE", "CCNPAUTO Lab 12")
room = client.create_room(title)
print(f"Created room: {room['title']} ({room['id']})")
message = client.post_message(room["id"], "**Lab 12:** Webex API connectivity and message delivery succeeded.")
print(f"Created message: {message['id']}")
items = client.messages(room["id"])
print(tabulate([[m.get("created"), m.get("personEmail"), m.get("text")] for m in items], headers=["Created", "Sender", "Text"]))
print(f"ROOM_ID={room['id']}")
