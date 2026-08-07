"""A small object-oriented Netmiko client for IOS XE."""

import logging
import time

from netmiko import ConnectHandler


logger = logging.getLogger(__name__)


class IOSXEDevice:
    def __init__(self, settings):
        self.settings = settings
        self.connection = None

    def connect(self):
        logger.info(
            "Opening IOS XE SSH session host=%s port=%s username=%s",
            self.settings.host,
            self.settings.ssh_port,
            self.settings.username,
        )
        started = time.perf_counter()
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
        logger.info(
            "IOS XE SSH session established elapsed_seconds=%.3f",
            time.perf_counter() - started,
        )

    def disconnect(self):
        if self.connection:
            logger.info("Closing IOS XE SSH session host=%s", self.settings.host)
            self.connection.disconnect()
            self.connection = None
            logger.debug("IOS XE SSH session closed")
        else:
            logger.debug("Disconnect requested with no active IOS XE SSH session")

    def send_and_parse(self, command):
        if not self.connection:
            raise RuntimeError("Connect to the device before sending a command")

        logger.info("Executing and parsing IOS XE command=%s", command)
        started = time.perf_counter()
        result = self.connection.send_command(command, use_textfsm=True)
        if isinstance(result, str):
            logger.error(
                "TextFSM parsing failed command=%s raw_length=%d",
                command,
                len(result),
            )
            raise RuntimeError(f"TextFSM could not parse: {command}")
        logger.info(
            "Command parsed command=%s records=%d elapsed_seconds=%.3f",
            command,
            len(result),
            time.perf_counter() - started,
        )
        logger.debug("Parsed command result command=%s data=%s", command, result)
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
        logger.debug("Normalized %d interface record(s)", len(interfaces))
        return interfaces

    def configure(self, commands):
        if not self.connection:
            raise RuntimeError("Connect to the device before sending configuration")
        logger.info("Sending %d IOS XE configuration command(s)", len(commands))
        logger.debug("Configuration commands=%s", commands)
        started = time.perf_counter()
        result = self.connection.send_config_set(commands)
        logger.info(
            "Configuration command set completed elapsed_seconds=%.3f",
            time.perf_counter() - started,
        )
        logger.debug("Configuration response=%s", result)
        return result
