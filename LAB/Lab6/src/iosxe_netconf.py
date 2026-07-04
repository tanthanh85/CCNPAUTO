"""Small ncclient adapter for IOS XE OSPF configuration."""

from ncclient import manager


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
        return manager.connect(
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

    def configure_ospf(self, payload):
        with self.connect() as session:
            reply = session.edit_config(target="running", config=payload, default_operation="merge")
            if not reply.ok:
                raise RuntimeError("NETCONF edit-config did not return <ok/>")
            return str(reply)

    def get_ospf_config(self):
        with self.connect() as session:
            reply = session.get_config(
                source="running", filter=("subtree", self.OSPF_FILTER)
            )
            return reply.data_xml

