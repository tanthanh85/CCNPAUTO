#!/usr/bin/env python3

from ncclient.operations import RPCError
from ncclient.transport.errors import SSHError

from src.netconf_client import NETCONFClient
from src.payloads import build_netconf_interfaces
from src.settings import Settings


client = None

try:
    settings = Settings()
    settings.confirm_changes()
    loopbacks = settings.loopbacks()
    payload = build_netconf_interfaces(loopbacks)

    client = NETCONFClient(settings)
    client.connect()

    for module in ("ietf-interfaces", "ietf-ip", "iana-if-type"):
        if not client.supports_module(module):
            raise RuntimeError(f"The NETCONF server did not advertise {module}")

    reply = client.edit_interfaces(payload)
    print(f"NETCONF edit-config accepted: {reply.ok}")

    verification = client.get_interfaces([item["name"] for item in loopbacks])
    print(verification.xml)

except PermissionError as error:
    print(f"Safety check stopped configuration: {error}")
except (RPCError, SSHError, TimeoutError) as error:
    print(f"NETCONF operation failed: {error}")
except (OSError, RuntimeError, ValueError) as error:
    print(f"Workflow stopped: {error}")
finally:
    if client:
        client.close()
