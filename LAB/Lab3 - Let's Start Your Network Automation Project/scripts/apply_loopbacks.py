#!/usr/bin/env python3

import logging
from pathlib import Path

import yaml
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

from src.iosxe_cli import IOSXEDevice
from src.logging_config import configure_logging
from src.loopback_source import LoopbackManager
from src.reporting import print_interfaces
from src.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging("apply_loopbacks", project_root=ROOT)
    logger.info("Starting loopback reconciliation")
    device = None

    try:
        settings = Settings()
        manager = LoopbackManager(
            ROOT / "data" / "loopbacks.yaml",
            ROOT / "templates" / "loopback.j2",
        )
        loopbacks = manager.load()
        logger.info("Validated %d loopback intent record(s)", len(loopbacks))
        logger.debug("Normalized loopback intent=%s", loopbacks)

        device = IOSXEDevice(settings)
        device.connect()

        before = device.get_interfaces()
        logger.info("Collected %d interface record(s) before change", len(before))
        print_interfaces(before, "Interfaces Before the Change")

        commands = manager.render(loopbacks)
        logger.info("Rendered %d IOS XE configuration command(s)", len(commands))
        logger.debug("Proposed IOS XE commands=%s", commands)
        print(f"Applying {len(loopbacks)} loopback interface(s)")
        output = device.configure(commands)
        logger.debug("Netmiko configuration response=%s", output)
        print(output)

        after = device.get_interfaces()
        logger.info("Collected %d interface record(s) after change", len(after))
        logger.debug("Observed interfaces after change=%s", after)
        print_interfaces(after, "Interfaces After the Change")

        observed = {item["interface"]: item for item in after}
        errors = []

        for loopback in loopbacks:
            name = f"Loopback{loopback['id']}"
            actual = observed.get(name)
            logger.debug(
                "Verifying interface=%s expected_ip=%s expected_enabled=%s "
                "observed=%s",
                name,
                loopback["ipv4"],
                loopback["enabled"],
                actual,
            )

            if actual is None:
                errors.append(f"{name} is missing")
            elif actual["ip_address"] != loopback["ipv4"]:
                errors.append(f"{name} has the wrong IP address")
            elif loopback["enabled"] and (
                actual["status"] != "up" or actual["protocol"] != "up"
            ):
                errors.append(f"{name} is not up/up")

        if errors:
            raise RuntimeError("; ".join(errors))

        logger.info("Verification passed for %d loopback(s)", len(loopbacks))
        print("Verification passed.")

    except yaml.YAMLError as error:
        logger.exception("Loopback YAML is invalid")
        print(f"The YAML file is not valid: {error}")
    except NetmikoAuthenticationException:
        logger.exception("IOS XE authentication failed; no configuration was sent")
        print("Authentication failed. No configuration was sent.")
    except NetmikoTimeoutException:
        logger.exception("IOS XE connection timed out")
        print("Connection timed out. Check the VPN and reservation details.")
    except (ValueError, RuntimeError) as error:
        logger.exception("Loopback reconciliation failed")
        print(f"The change failed: {error}")
    finally:
        if device:
            device.disconnect()
        logger.info("Loopback reconciliation finished")


if __name__ == "__main__":
    main()
