#!/usr/bin/env python3
"""Re-enable IOS XE Loopback1 after receiving its shutdown syslog event."""

from __future__ import annotations

import configparser
import logging
import os
import re
import signal
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)


SHUTDOWN_EVENT = re.compile(
    r"%LINK-\d+-(?:CHANGED|UPDOWN):\s+Interface\s+Loopback1,\s+"
    r"changed state to administratively down\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RouterSettings:
    host: str
    port: int
    username: str
    password: str
    device_type: str
    timeout: int
    syslog_source: str | None = None

    def device_dictionary(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "device_type": self.device_type,
            "timeout": self.timeout,
        }


def load_settings(path: Path) -> RouterSettings:
    """Load SSH settings from app-hosting environment variables or a local file."""

    # IOS XE app-hosting supplies these values through Docker run options. The
    # INI fallback keeps local development and unit testing straightforward.
    environment = {
        "host": os.getenv("ROUTER_HOST"),
        "username": os.getenv("ROUTER_USERNAME"),
        "password": os.getenv("ROUTER_PASSWORD"),
    }
    if any(environment.values()):
        missing = [name for name, value in environment.items() if not value]
        if missing:
            raise ValueError(
                "Incomplete router environment configuration; missing: "
                + ", ".join(missing)
            )
        return RouterSettings(
            host=str(environment["host"]),
            port=int(os.getenv("ROUTER_PORT", "22")),
            username=str(environment["username"]),
            password=str(environment["password"]),
            device_type=os.getenv("ROUTER_DEVICE_TYPE", "cisco_ios"),
            timeout=int(os.getenv("ROUTER_TIMEOUT", "10")),
            syslog_source=os.getenv("ROUTER_SYSLOG_SOURCE"),
        )

    parser = configparser.ConfigParser()
    if not parser.read(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    section = parser["router"]
    password = section.get("password", "")
    if not password or password == "REPLACE_WITH_LAB_PASSWORD":
        raise ValueError("Replace the placeholder password before packaging")

    return RouterSettings(
        host=section.get("host", "192.168.200.1"),
        port=section.getint("port", 22),
        username=section.get("username", "apphost"),
        password=password,
        device_type=section.get("device_type", "cisco_ios"),
        timeout=section.getint("timeout", 10),
        syslog_source=section.get("syslog_source", fallback=None),
    )


def is_loopback1_shutdown(message: str) -> bool:
    """Return True only for the Loopback1 administrative-down LINK event."""

    return SHUTDOWN_EVENT.search(message) is not None


class LoopbackRecovery:
    """Use Netmiko to issue `no shutdown` under Loopback1."""

    def __init__(
        self,
        settings: RouterSettings,
        connection_factory: Callable = ConnectHandler,
    ) -> None:
        self.settings = settings
        self.connection_factory = connection_factory

    def enable_loopback1(self) -> bool:
        """Connect, enable the interface, verify its state, and disconnect."""

        connection = None
        try:
            device = self.settings.device_dictionary()
            connection = self.connection_factory(**device)
            output = connection.send_config_set(
                ["interface Loopback1", "no shutdown"]
            )
            verification = connection.send_command(
                "show interfaces Loopback1 | include line protocol"
            )
            logging.info("Netmiko configuration output: %s", output.strip())
            logging.info("Loopback1 verification: %s", verification.strip())
            return "loopback1 is up, line protocol is up" in verification.lower()
        except NetmikoAuthenticationException:
            logging.exception("Netmiko authentication failed")
            return False
        except NetmikoTimeoutException:
            logging.exception("Netmiko connection timed out")
            return False
        except Exception:
            logging.exception("Unexpected Netmiko recovery failure")
            return False
        finally:
            if connection is not None:
                connection.disconnect()


class SyslogRecoveryServer:
    """Listen for the shutdown event and invoke the Netmiko remediator."""

    def __init__(
        self,
        host: str,
        port: int,
        expected_source: str,
        recovery: LoopbackRecovery,
    ) -> None:
        self.host = host
        self.port = port
        self.expected_source = expected_source
        self.recovery = recovery
        self.stop_event = threading.Event()
        self.socket: socket.socket | None = None

    def stop(self, *_args: object) -> None:
        self.stop_event.set()
        if self.socket is not None:
            self.socket.close()

    def process_datagram(
        self,
        payload: bytes,
        source: tuple[str, int],
    ) -> bool:
        """Validate source and event before attempting recovery."""

        if source[0] != self.expected_source:
            logging.warning("Ignored syslog from unexpected source %s", source[0])
            return False

        message = payload.decode("utf-8", errors="replace").replace("\n", " ")
        if not is_loopback1_shutdown(message):
            logging.debug("Ignored unrelated syslog from %s", source[0])
            return False

        logging.warning("Detected Loopback1 administrative shutdown")
        return self.recovery.enable_loopback1()

    def serve_forever(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.socket.settimeout(1.0)
        logging.info("Listening for IOS XE syslog on udp://%s:%s", self.host, self.port)

        while not self.stop_event.is_set():
            try:
                payload, source = self.socket.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                if self.stop_event.is_set():
                    break
                raise
            self.process_datagram(payload, source)


def main() -> None:
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)sZ %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    config_path = Path(
        os.getenv("CAF_APP_CONFIG_FILE", "/data/package_config.ini")
    )
    settings = load_settings(config_path)
    server = SyslogRecoveryServer(
        host=os.getenv("SYSLOG_HOST", "0.0.0.0"),
        port=int(os.getenv("SYSLOG_PORT", "5514")),
        expected_source=(
            os.getenv("ROUTER_SYSLOG_SOURCE")
            or settings.syslog_source
            or settings.host
        ),
        recovery=LoopbackRecovery(settings),
    )
    signal.signal(signal.SIGTERM, server.stop)
    signal.signal(signal.SIGINT, server.stop)
    server.serve_forever()


if __name__ == "__main__":
    main()
