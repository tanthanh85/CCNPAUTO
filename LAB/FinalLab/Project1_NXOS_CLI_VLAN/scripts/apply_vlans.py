from __future__ import annotations

import argparse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from netmiko import ConnectHandler

from src.device import device
from src.vlan_source import load_vlan_intent


def render_vlan_config() -> str:
    vlans = load_vlan_intent()
    env = Environment(
        loader=FileSystemLoader("templates"),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("vlans.j2")
    return template.render(vlans=vlans)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Render configuration without connecting")
    args = parser.parse_args()

    rendered = render_vlan_config()
    print("Rendered NX-OS configuration:")
    print("-" * 60)
    print(rendered)
    print("-" * 60)

    if args.dry_run:
        return

    commands = [line for line in rendered.splitlines() if line.strip()]

    with ConnectHandler(**device) as connection:
        output = connection.send_config_set(commands)
        print(output)
        print(connection.send_command("show vlan brief"))


if __name__ == "__main__":
    main()
