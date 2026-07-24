from __future__ import annotations

import argparse

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from ncclient import manager

from src.route_source import load_static_routes
from src.settings import load_settings


def render_static_route_payload() -> str:
    routes = load_static_routes()
    env = Environment(
        loader=FileSystemLoader("templates"),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("static_routes.xml.j2")
    return template.render(static_routes=routes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Render XML without connecting")
    args = parser.parse_args()

    payload = render_static_route_payload()
    print("Rendered NETCONF payload:")
    print("-" * 70)
    print(payload)
    print("-" * 70)

    if args.dry_run:
        return

    settings = load_settings()
    with manager.connect(
        host=settings.host,
        port=settings.netconf_port,
        username=settings.username,
        password=settings.password,
        hostkey_verify=False,
        look_for_keys=False,
        allow_agent=False,
        timeout=30,
    ) as connection:
        response = connection.edit_config(target="running", config=payload)
        print(response)


if __name__ == "__main__":
    main()

