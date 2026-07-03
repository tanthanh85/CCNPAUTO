"""Small Netmiko helper functions for IOS XE."""

from netmiko import ConnectHandler


def connect(settings):
    return ConnectHandler(
        device_type="cisco_ios",
        host=settings["host"],
        port=settings["ssh_port"],
        username=settings["username"],
        password=settings["password"],
        conn_timeout=20,
        banner_timeout=30,
        fast_cli=False,
    )


def send_and_parse(connection, command):
    result = connection.send_command(command, use_textfsm=True)
    if isinstance(result, str):
        raise RuntimeError(f"TextFSM could not parse: {command}")
    return result


def get_version(connection):
    return send_and_parse(connection, "show version")


def get_interfaces(connection):
    parsed_output = send_and_parse(connection, "show ip interface brief")
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
