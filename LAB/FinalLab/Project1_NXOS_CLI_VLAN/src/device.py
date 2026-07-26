from __future__ import annotations

from src.settings import load_settings


settings = load_settings()


# The connection values are already mapped from the runtime settings.
# Troubleshoot the remaining dictionary problem before running the connection.
# The apply script will use: ConnectHandler(**device)
device = {
    "host": settings.host,
    "username": settings.username,
    "password": settings.password,
    "port": settings.port,
}
