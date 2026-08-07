from __future__ import annotations

import logging

from dotenv import load_dotenv

from netconf_to_splunk import Settings, SplunkHEC


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    client = SplunkHEC(settings)
    client.send_cpu_event(
        {
            "device": "hec-self-test",
            "subscription_id": "test",
            "event_time": None,
            "cpu_five_seconds": 0,
        }
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.info("Splunk HEC accepted the validation event.")


if __name__ == "__main__":
    main()
