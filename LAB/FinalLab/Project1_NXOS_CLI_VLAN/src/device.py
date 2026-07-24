from __future__ import annotations

from src.settings import load_settings


settings = load_settings()


# TODO: Complete this Netmiko device dictionary.
# The apply script will use: ConnectHandler(**device)
device = {
    # "device_type": "REPLACE_ME",
    # "host": settings.host,
    # "username": settings.username,
    # "password": settings.password,
    # "port": settings.port,
}
