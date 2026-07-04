"""Display deterministic RESTCONF data before introducing the language model."""

import json

from src.restconf_client import IOSXERoutingClient, RestconfError


def main() -> None:
    try:
        client = IOSXERoutingClient()
        print(json.dumps(client.summary(), indent=2))
        print(json.dumps(client.filtered_routes(limit=5), indent=2))
    except RestconfError as exc:
        raise SystemExit(f"RESTCONF check failed: {exc}") from exc


if __name__ == "__main__":
    main()

