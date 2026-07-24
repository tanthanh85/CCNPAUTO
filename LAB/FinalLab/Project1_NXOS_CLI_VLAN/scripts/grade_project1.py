from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from dotenv import dotenv_values
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def print_result(name: str, points: int, maximum: int, detail: str) -> None:
    print(f"{name}: {points}/{maximum} - {detail}")


def grade_env() -> int:
    env_file = ROOT / ".env"
    if not env_file.exists():
        print_result("Task 1 credentials", 0, 10, ".env file not found")
        return 0

    values = dotenv_values(env_file)
    required = ["NXOS_HOST", "NXOS_USERNAME", "NXOS_PASSWORD", "NXOS_PORT"]
    missing = [key for key in required if not values.get(key)]
    placeholders = [
        key
        for key in required
        if str(values.get(key, "")).startswith("REPLACE_WITH")
    ]

    if missing or placeholders:
        print_result("Task 1 credentials", 0, 10, f"missing/placeholders: {missing + placeholders}")
        return 0

    print_result("Task 1 credentials", 10, 10, ".env contains required NX-OS connection values")
    return 10


def grade_template() -> int:
    try:
        data = yaml.safe_load((ROOT / "data/vlans.yaml").read_text(encoding="utf-8"))
        env = Environment(
            loader=FileSystemLoader(ROOT / "templates"),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        rendered = env.get_template("vlans.j2").render(vlans=data["vlans"])
    except Exception as exc:
        print_result("Task 2 Jinja2 template", 0, 10, f"template failed: {exc}")
        return 0

    required_fragments = ["vlan 10", "name IT", "vlan 20", "name HR"]
    missing = [item for item in required_fragments if item not in rendered]
    if missing:
        print_result("Task 2 Jinja2 template", 0, 10, f"rendered output missing: {missing}")
        return 0

    if "{%" not in (ROOT / "templates/vlans.j2").read_text(encoding="utf-8"):
        print_result("Task 2 Jinja2 template", 5, 10, "output works, but no Jinja2 loop was detected")
        return 5

    print_result("Task 2 Jinja2 template", 10, 10, "template renders VLAN configuration correctly")
    return 10


def grade_device_dictionary() -> int:
    try:
        os.environ["NXOS_HOST"] = "nxos.example.test"
        os.environ["NXOS_USERNAME"] = "admin"
        os.environ["NXOS_PASSWORD"] = "password"
        os.environ["NXOS_PORT"] = "22"
        sys.modules.pop("src.device", None)
        from src.device import device
    except Exception as exc:
        print_result("Task 3 device dictionary", 0, 10, f"device dictionary failed: {exc}")
        return 0

    expected = {
        "device_type": "cisco_nxos",
        "host": "nxos.example.test",
        "username": "admin",
        "password": "password",
        "port": 22,
    }
    missing_or_wrong = [key for key, value in expected.items() if device.get(key) != value]
    if missing_or_wrong:
        print_result("Task 3 device dictionary", 0, 10, f"missing/wrong keys: {missing_or_wrong}")
        return 0

    print_result("Task 3 device dictionary", 10, 10, "Netmiko device dictionary is correct")
    return 10


def main() -> None:
    print("Project 1 Self-Grading")
    print("=" * 60)
    score = grade_env() + grade_template() + grade_device_dictionary()
    print("=" * 60)
    print(f"Project 1 score: {score}/30")


if __name__ == "__main__":
    main()
