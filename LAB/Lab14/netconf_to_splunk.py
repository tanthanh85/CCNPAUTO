from __future__ import annotations

import logging
import os
import signal
import time
from dataclasses import dataclass
from typing import Any
from xml.parsers.expat import ExpatError

import requests
import urllib3
import xmltodict
from dotenv import load_dotenv
from ncclient import manager
from ncclient.xml_ import to_ele


SUBSCRIPTION_RPC = """
<establish-subscription
    xmlns="urn:ietf:params:xml:ns:yang:ietf-event-notifications"
    xmlns:yp="urn:ietf:params:xml:ns:yang:ietf-yang-push"
    xmlns:cpu="http://cisco.com/ns/yang/Cisco-IOS-XE-process-cpu-oper">
  <stream>yp:yang-push</stream>
  <yp:xpath-filter>/cpu:cpu-usage/cpu-utilization/five-seconds</yp:xpath-filter>
  <yp:period>{period}</yp:period>
</establish-subscription>
""".strip()

LOG = logging.getLogger("netconf_to_splunk")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    iosxe_host: str
    iosxe_port: int
    iosxe_username: str
    iosxe_password: str
    iosxe_hostkey_verify: bool
    splunk_hec_url: str
    splunk_hec_token: str
    splunk_verify_tls: bool
    splunk_index: str
    period: int
    notification_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        required = [
            "IOSXE_HOST",
            "IOSXE_USERNAME",
            "IOSXE_PASSWORD",
            "SPLUNK_HEC_URL",
            "SPLUNK_HEC_TOKEN",
        ]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        period = int(os.getenv("SUBSCRIPTION_PERIOD", "500"))
        if period < 100:
            raise ValueError("SUBSCRIPTION_PERIOD must be at least 100 centiseconds.")

        return cls(
            iosxe_host=os.environ["IOSXE_HOST"],
            iosxe_port=int(os.getenv("IOSXE_NETCONF_PORT", "830")),
            iosxe_username=os.environ["IOSXE_USERNAME"],
            iosxe_password=os.environ["IOSXE_PASSWORD"],
            iosxe_hostkey_verify=env_bool("IOSXE_HOSTKEY_VERIFY", False),
            splunk_hec_url=os.environ["SPLUNK_HEC_URL"].rstrip("/"),
            splunk_hec_token=os.environ["SPLUNK_HEC_TOKEN"],
            splunk_verify_tls=env_bool("SPLUNK_HEC_VERIFY_TLS", False),
            splunk_index=os.getenv("SPLUNK_INDEX", "network_telemetry"),
            period=period,
            notification_timeout=int(os.getenv("NOTIFICATION_TIMEOUT", "30")),
        )


class SplunkHEC:
    def __init__(self, settings: Settings) -> None:
        self.url = f"{settings.splunk_hec_url}/services/collector/event"
        self.token = settings.splunk_hec_token
        self.verify_tls = settings.splunk_verify_tls
        self.index = settings.splunk_index
        self.session = requests.Session()

        if not self.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def send_cpu_event(self, event: dict[str, object]) -> None:
        payload = {
            "time": time.time(),
            "host": event["device"],
            "source": "netconf-yang-push",
            "sourcetype": "cisco:iosxe:netconf:cpu",
            "index": self.index,
            "event": event,
        }
        response = self.session.post(
            self.url,
            headers={"Authorization": f"Splunk {self.token}"},
            json=payload,
            timeout=10,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"Splunk HEC rejected the event: {result}")


class IOSXENetconfCPUCollector:
    def __init__(self, settings: Settings, splunk: SplunkHEC) -> None:
        self.settings = settings
        self.splunk = splunk
        self.running = True

    @staticmethod
    def _local_name(key: str) -> str:
        """Return a local XML name for the subscription RPC reply parser."""
        return key.rsplit(":", maxsplit=1)[-1].lstrip("@")

    @classmethod
    def _find_first_scalar(
        cls,
        node: Any,
        wanted_names: set[str],
    ) -> str | None:
        """Find a scalar in an RPC reply whose exact wrapper may vary by release."""
        if isinstance(node, dict):
            # Check the current level before descending into child elements.
            for key, value in node.items():
                if cls._local_name(str(key)) in wanted_names:
                    # A leaf with its own xmlns attribute is represented as
                    # {"@xmlns": "...", "#text": "value"} by xmltodict.
                    if isinstance(value, dict) and "#text" in value:
                        value = value["#text"]
                    if not isinstance(value, (dict, list)) and value is not None:
                        return str(value).strip()

            for value in node.values():
                found = cls._find_first_scalar(value, wanted_names)
                if found is not None:
                    return found

        elif isinstance(node, list):
            for item in node:
                found = cls._find_first_scalar(item, wanted_names)
                if found is not None:
                    return found

        return None

    @staticmethod
    def _xml_to_dict(xml_text: str) -> dict[str, Any]:
        """Parse trusted NETCONF XML into normal Python dictionaries."""
        try:
            parsed = xmltodict.parse(
                xml_text,
                disable_entities=True,
            )
        except (ExpatError, TypeError) as exc:
            raise ValueError(f"Invalid NETCONF XML: {exc}") from exc

        if not isinstance(parsed, dict):
            raise ValueError("NETCONF XML did not produce a dictionary root.")
        return parsed

    def _parse_notification(self, xml_text: str, subscription_id: str) -> dict[str, object] | None:
        document = self._xml_to_dict(xml_text)
        notification = document.get("notification")
        if not isinstance(notification, dict):
            raise ValueError("XML does not contain a notification dictionary.")

        # IOS XE sends the sample with default namespaces. xmltodict therefore
        # keeps the element names below as normal, unprefixed dictionary keys.
        push_update = notification.get("push-update")
        if not isinstance(push_update, dict):
            return None

        try:
            cpu_text = push_update["datastore-contents-xml"]["cpu-usage"][
                "cpu-utilization"
            ]["five-seconds"]
        except (KeyError, TypeError):
            # The NETCONF session can carry notifications unrelated to this
            # CPU subscription. They are valid XML but not CPU samples.
            return None

        if isinstance(cpu_text, dict):
            cpu_text = cpu_text.get("#text")
        if cpu_text is None or isinstance(cpu_text, (dict, list)):
            raise ValueError("five-seconds does not contain a scalar value.")
        cpu_text = str(cpu_text).strip()

        try:
            cpu_value = int(cpu_text)
        except ValueError as exc:
            raise ValueError(
                f"Notification contains a non-integer five-seconds value: {cpu_text!r}"
            ) from exc

        if not 0 <= cpu_value <= 100:
            raise ValueError(
                f"Notification contains an out-of-range CPU value: {cpu_value}"
            )

        return {
            "device": self.settings.iosxe_host,
            "subscription_id": str(
                push_update.get("subscription-id") or subscription_id
            ),
            "event_time": notification.get("eventTime"),
            "cpu_five_seconds": cpu_value,
        }

    def stop(self, *_args: object) -> None:
        self.running = False

    def run(self) -> None:
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        with manager.connect(
            host=self.settings.iosxe_host,
            port=self.settings.iosxe_port,
            username=self.settings.iosxe_username,
            password=self.settings.iosxe_password,
            hostkey_verify=self.settings.iosxe_hostkey_verify,
            allow_agent=False,
            look_for_keys=False,
            timeout=30,
        ) as session:
            LOG.info(
                "Connected to IOS XE NETCONF at %s:%s",
                self.settings.iosxe_host,
                self.settings.iosxe_port,
            )

            operation = SUBSCRIPTION_RPC.format(period=self.settings.period)
            reply = session.dispatch(to_ele(operation))
            reply_data = self._xml_to_dict(reply.xml)
            subscription_id = self._find_first_scalar(
                reply_data,
                {"subscription-id", "id"},
            )
            if not subscription_id:
                raise RuntimeError(f"Subscription was not accepted: {reply.xml}")

            LOG.info("Subscription established: %s", subscription_id)

            while self.running:
                notification = session.take_notification(
                    timeout=self.settings.notification_timeout
                )
                if notification is None:
                    LOG.warning("No notification received before timeout.")
                    continue

                try:
                    event = self._parse_notification(
                        notification.notification_xml,
                        subscription_id,
                    )
                except ValueError as exc:
                    LOG.warning("Ignored malformed NETCONF notification: %s", exc)
                    continue
                if event is None:
                    LOG.debug("Ignored notification without five-seconds CPU data.")
                    continue

                try:
                    self.splunk.send_cpu_event(event)
                    LOG.info(
                        "Forwarded CPU sample: device=%s cpu_five_seconds=%s",
                        event["device"],
                        event["cpu_five_seconds"],
                    )
                except (requests.RequestException, RuntimeError) as exc:
                    LOG.error("Splunk HEC delivery failed: %s", exc)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    collector = IOSXENetconfCPUCollector(settings, SplunkHEC(settings))
    collector.run()


if __name__ == "__main__":
    main()
