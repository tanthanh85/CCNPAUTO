from __future__ import annotations

import logging
import os
import signal
import time
from dataclasses import dataclass

import requests
import urllib3
from dotenv import load_dotenv
from lxml import etree
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
    def _first_text(root: etree._Element, local_name: str) -> str | None:
        values = root.xpath(f"//*[local-name()='{local_name}']/text()")
        return str(values[0]).strip() if values else None

    def _parse_notification(self, xml_text: str, subscription_id: str) -> dict[str, object] | None:
        root = etree.fromstring(xml_text.encode("utf-8"))
        cpu_text = self._first_text(root, "five-seconds")
        if cpu_text is None:
            return None

        return {
            "device": self.settings.iosxe_host,
            "subscription_id": self._first_text(root, "subscription-id") or subscription_id,
            "event_time": self._first_text(root, "eventTime"),
            "cpu_five_seconds": int(cpu_text),
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
            reply_root = etree.fromstring(reply.xml.encode("utf-8"))
            subscription_id = self._first_text(reply_root, "subscription-id")
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

                event = self._parse_notification(
                    notification.notification_xml,
                    subscription_id,
                )
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
