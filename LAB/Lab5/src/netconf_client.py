"""A small NETCONF client for the IETF interface workflow."""

from ncclient import manager


class NETCONFClient:
    def __init__(self, settings):
        self.settings = settings
        self.connection = None

    def connect(self):
        self.connection = manager.connect(
            host=self.settings.host,
            port=self.settings.netconf_port,
            username=self.settings.username,
            password=self.settings.password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            device_params={"name": "iosxe"},
            timeout=30,
        )

    def supports_module(self, module_name):
        return any(module_name in capability for capability in self.connection.server_capabilities)

    def edit_interfaces(self, interfaces_xml):
        return self.connection.edit_config(
            target="running",
            config=interfaces_xml,
            default_operation="merge",
            error_option="rollback-on-error",
        )

    def get_interfaces(self, names):
        name_filters = "".join(f"<interface><name>{name}</name></interface>" for name in names)
        filter_xml = (
            '<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">'
            f"{name_filters}</interfaces>"
        )
        return self.connection.get_config(source="running", filter=("subtree", filter_xml))

    def close(self):
        if self.connection:
            self.connection.close_session()
