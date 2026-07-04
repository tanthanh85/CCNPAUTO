#!/usr/bin/env python3
"""Configure OSPF area 0 for every NetBox-managed loopback through NETCONF."""

import os

from ncclient.operations import RPCError
from ncclient.transport.errors import AuthenticationError, SSHError

from src.iosxe_netconf import IOSXENETCONF
from src.netbox_source import NetBoxLoopbackSource
from src.ospf_renderer import OSPFRenderer
from src.settings import Settings


def main():
    settings = Settings()
    settings.confirm_write_access()
    source = NetBoxLoopbackSource(
        settings.netbox_url,
        settings.netbox_token,
        settings.netbox_device,
        settings.netbox_tag,
    )
    loopbacks = source.load()
    payload = OSPFRenderer().render(
        loopbacks,
        process_id=os.getenv("OSPF_PROCESS_ID", "1"),
        area=os.getenv("OSPF_AREA", "0"),
    )
    print("Rendered NETCONF payload:\n")
    print(payload)

    client = IOSXENETCONF(settings)
    print("\nNETCONF edit-config reply:")
    print(client.configure_ospf(payload))
    running = client.get_ospf_config()
    print("\nRunning OSPF configuration returned by NETCONF:")
    print(running)

    missing = [item["ipv4"] for item in loopbacks if item["ipv4"] not in running]
    if missing:
        raise RuntimeError(f"OSPF verification is missing: {', '.join(missing)}")
    print(f"PASS: OSPF area 0 contains all {len(loopbacks)} managed loopback(s).")


if __name__ == "__main__":
    try:
        main()
    except PermissionError as exc:
        raise SystemExit(f"Safety check stopped the change: {exc}") from exc
    except AuthenticationError as exc:
        raise SystemExit("NETCONF authentication failed") from exc
    except SSHError as exc:
        raise SystemExit(f"NETCONF SSH connection failed: {exc}") from exc
    except RPCError as exc:
        raise SystemExit(f"IOS XE rejected the NETCONF payload: {exc}") from exc
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"OSPF configuration failed: {exc}") from exc

