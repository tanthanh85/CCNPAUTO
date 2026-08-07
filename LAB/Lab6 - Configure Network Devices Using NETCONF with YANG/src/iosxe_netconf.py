"""Small ncclient adapter for IOS XE OSPF configuration."""

import logging
import time

from ncclient import manager


logger = logging.getLogger(__name__)


class IOSXENETCONF:
    OSPF_FILTER = """
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <router>
          <router-ospf xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ospf">
            <ospf/>
          </router-ospf>
        </router>
      </native>
    """

    def __init__(self, settings):
        self.settings = settings

    def connect(self):
        logger.info(
            "Opening NETCONF session host=%s port=%s username=%s",
            self.settings.host,
            self.settings.netconf_port,
            self.settings.username,
        )
        started = time.perf_counter()
        session = manager.connect(
            host=self.settings.host,
            port=self.settings.netconf_port,
            username=self.settings.username,
            password=self.settings.password,
            hostkey_verify=False,
            device_params={"name": "iosxe"},
            allow_agent=False,
            look_for_keys=False,
            timeout=30,
        )
        logger.info(
            "NETCONF session established session_id=%s elapsed_seconds=%.3f",
            getattr(session, "session_id", "unknown"),
            time.perf_counter() - started,
        )
        logger.debug("Server advertised capabilities=%s", list(session.server_capabilities))
        return session

    def configure_ospf(self, payload):
        logger.info("Sending NETCONF edit-config target=running default_operation=merge")
        started = time.perf_counter()
        with self.connect() as session:
            reply = session.edit_config(target="running", config=payload, default_operation="merge")
            if not reply.ok:
                raise RuntimeError("NETCONF edit-config did not return <ok/>")
            logger.info(
                "NETCONF edit-config succeeded elapsed_seconds=%.3f",
                time.perf_counter() - started,
            )
            return str(reply)

    def get_ospf_config(self):
        logger.info("Reading running OSPF configuration with subtree filter")
        logger.debug("OSPF subtree filter=%s", self.OSPF_FILTER)
        started = time.perf_counter()
        with self.connect() as session:
            reply = session.get_config(
                source="running", filter=("subtree", self.OSPF_FILTER)
            )
            logger.info(
                "NETCONF get-config completed elapsed_seconds=%.3f",
                time.perf_counter() - started,
            )
            return reply.data_xml
