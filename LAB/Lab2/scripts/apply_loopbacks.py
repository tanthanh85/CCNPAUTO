#!/usr/bin/env python3

from pathlib import Path

from src.iosxe_cli import connect, get_interfaces
from src.loopback_source import load_loopbacks, render_commands
from src.reporting import print_interfaces
from src.settings import confirm_write_access, load_settings


ROOT = Path(__file__).resolve().parents[1]
BATCH_SIZE = 20

settings = load_settings()
confirm_write_access(settings)
loopbacks = load_loopbacks(ROOT / "data" / "loopbacks.yaml")

connection = connect(settings)

try:
    before = get_interfaces(connection)
    print_interfaces(before, "Interfaces Before the Change")

    # Configure no more than 20 loopbacks in each batch.
    for start in range(0, len(loopbacks), BATCH_SIZE):
        batch = loopbacks[start : start + BATCH_SIZE]
        commands = []

        for loopback in batch:
            commands.extend(render_commands(loopback, ROOT / "templates"))

        print(f"Applying loopbacks {start + 1}-{start + len(batch)}")
        print(connection.send_config_set(commands))

    after = get_interfaces(connection)
finally:
    connection.disconnect()

print_interfaces(after, "Interfaces After the Change")

# Verify every interface and address from the YAML file.
observed = {item["interface"]: item for item in after}
errors = []

for loopback in loopbacks:
    name = f"Loopback{loopback['id']}"
    actual = observed.get(name)
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

print("Verification passed.")
