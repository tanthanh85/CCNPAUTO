#!/usr/bin/env python3
"""Send a representative Loopback1 shutdown event to the local container."""

import socket


MESSAGE = (
    "<189>IOSXE: %LINK-5-CHANGED: Interface Loopback1, "
    "changed state to administratively down"
)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
    client.sendto(MESSAGE.encode(), ("127.0.0.1", 15514))

print("Sent Loopback1 shutdown test event to udp://127.0.0.1:15514")
