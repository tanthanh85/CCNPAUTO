from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class NxosSettings:
    host: str
    username: str
    password: str
    port: int = 22


def load_settings() -> NxosSettings:
    return NxosSettings(
        host=os.getenv("NXOS_HOST", ""),
        username=os.getenv("NXOS_USERNAME", ""),
        password=os.getenv("NXOS_PASSWORD", ""),
        port=int(os.getenv("NXOS_PORT", "22")),
    )

