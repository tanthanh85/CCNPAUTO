#!/usr/bin/env python3
"""Apply loopback source-of-truth data through a Jinja2 CLI template."""

from pathlib import Path

from src.iosxe_cli import IOSXECLIClient
from src.loopback_source import load_loopbacks, render_commands
from src.reporting import print_interfaces
from src.settings import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = Settings.from_env()
    settings.require_reserved_write_access()
    loopbacks = load_loopbacks(PROJECT_ROOT / "data" / "loopbacks.yaml")

    with IOSXECLIClient(settings) as device:
        before = device.collect_interfaces()
        print_interfaces(before, "Interfaces Before the Source-of-Truth Change")

        for loopback in loopbacks:
            commands = render_commands(loopback, PROJECT_ROOT / "templates")
            print(f"\nApplying Loopback{loopback['id']} from YAML:")
            for command in commands:
                print(f"  {command}")
            result = device.send_config(commands)
            print(result)

        after = device.collect_interfaces()

    print_interfaces(after, "Interfaces After the Source-of-Truth Change")

    observed = {row["interface"]: row for row in after}
    failures: list[str] = []
    for item in loopbacks:
        name = f"Loopback{item['id']}"
        actual = observed.get(name)
        if actual is None:
            failures.append(f"{name} is missing")
            continue
        if actual["ip_address"] != item["ipv4"]:
            failures.append(
                f"{name} has {actual['ip_address']} instead of {item['ipv4']}"
            )
        if item["enabled"] and (
            actual["status"] != "up" or actual["protocol"] != "up"
        ):
            failures.append(
                f"{name} expected up/up but is "
                f"{actual['status']}/{actual['protocol']}"
            )
    if failures:
        raise RuntimeError("Verification failed: " + "; ".join(failures))
    print("\nVerification passed: YAML intent matches the CLI interface state.")


if __name__ == "__main__":
    main()
