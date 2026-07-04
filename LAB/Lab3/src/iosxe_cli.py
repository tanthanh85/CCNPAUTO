"""A small object-oriented Netmiko client for IOS XE."""

from netmiko import ConnectHandler


class IOSXEDevice:
    def __init__(self, settings):
        self.settings = settings
        self.connection = None

    def connect(self):
        self.connection = ConnectHandler(
            device_type="cisco_ios",
            host=self.settings.host,
            port=self.settings.ssh_port,
            username=self.settings.username,
            password=self.settings.password,
            conn_timeout=20,
            banner_timeout=30,
            fast_cli=False,
        )

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            self.connection = None

    def send_and_parse(self, command):
        if not self.connection:
            raise RuntimeError("Connect to the device before sending a command")

        result = self.connection.send_command(command, use_textfsm=True)
        if isinstance(result, str):
            raise RuntimeError(f"TextFSM could not parse: {command}")
        return result

    def get_version(self):
        return self.send_and_parse("show version")

    def get_interfaces(self):
        parsed_output = self.send_and_parse("show ip interface brief")
        interfaces = []

        for item in parsed_output:
            interfaces.append(
                {
                    "interface": item.get("interface", "-"),
                    "ip_address": item.get("ip_address", "unassigned"),
                    "status": item.get("status", "unknown"),
                    "protocol": item.get("proto", "unknown"),
                }
            )
        return interfaces

    def configure(self, commands):
        if not self.connection:
            raise RuntimeError("Connect to the device before sending configuration")
        return self.connection.send_config_set(commands)
