from __future__ import annotations

import ast
import contextlib
import importlib
import importlib.util
import io
import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS: list[tuple[str, int, int, str]] = []


def print_result(
    name: str,
    points: int,
    maximum: int,
    detail: str,
    expected: str,
) -> None:
    print(f"{name}: {points}/{maximum} - {detail}")
    RESULTS.append((name, points, maximum, expected))
    if points < maximum:
        print(f"  Expected for full points: {expected}")


def grade_dependency() -> int:
    if importlib.util.find_spec("jinja2") is None:
        print_result(
            "Task 1 Python dependency",
            0,
            10,
            "the template-rendering module imported by apply_vlans.py is unavailable",
            "Read the ModuleNotFoundError and scripts/apply_vlans.py, identify "
            "which distribution supplies the missing template module, and "
            "install it in the active final_lab1 environment.",
        )
        return 0

    try:
        template_module = importlib.import_module("jinja2")
    except ImportError as exc:
        print_result(
            "Task 1 Python dependency",
            0,
            10,
            f"the template-rendering module could not be imported: {exc}",
            "Install the package that supplies the imported template module "
            "in the active final_lab1 environment.",
        )
        return 0

    version = getattr(template_module, "__version__", "unknown")
    print_result(
        "Task 1 Python dependency",
        10,
        10,
        f"required template module is importable (version {version})",
        "The missing template-rendering dependency is installed in final_lab1.",
    )
    return 10


def grade_env() -> int:
    env_file = ROOT / ".env"
    if not env_file.exists():
        print_result(
            "Task 2 runtime configuration",
            0,
            10,
            "required local runtime configuration file not found",
            "Trace scripts/apply_vlans.py through src/device.py and "
            "src/settings.py, then create the local dotenv file with every "
            "runtime value expected by the settings class.",
        )
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
        print_result(
            "Task 2 runtime configuration",
            0,
            10,
            f"missing or placeholder fields: {missing + placeholders}",
            "Replace every required NX-OS runtime value with the active "
            "sandbox reservation value.",
        )
        return 0

    print_result(
        "Task 2 runtime configuration",
        10,
        10,
        "runtime configuration contains required NX-OS connection values",
        "All four required values are present and are not placeholders.",
    )
    return 10


def grade_template() -> int:
    try:
        import yaml
        from jinja2 import Environment, FileSystemLoader, StrictUndefined

        data = yaml.safe_load((ROOT / "data/vlans.yaml").read_text(encoding="utf-8"))
        env = Environment(
            loader=FileSystemLoader(ROOT / "templates"),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        rendered = env.get_template("vlans.j2").render(vlans=data["vlans"])
    except Exception as exc:
        print_result(
            "Task 3 Jinja2 template",
            0,
            10,
            f"template could not render: {type(exc).__name__}: {exc}",
            "templates/vlans.j2 must loop over vlans and render each VLAN ID "
            "and name as valid NX-OS CLI.",
        )
        return 0

    required_fragments = ["vlan 10", "name IT", "vlan 20", "name HR"]
    missing = [item for item in required_fragments if item not in rendered]
    if missing:
        print_result(
            "Task 3 Jinja2 template",
            0,
            10,
            f"rendered output is missing: {missing}",
            "Render vlan 10/name IT and vlan 20/name HR from the supplied "
            "YAML without hard-coding the records in Python.",
        )
        return 0

    if "{%" not in (ROOT / "templates/vlans.j2").read_text(encoding="utf-8"):
        print_result(
            "Task 3 Jinja2 template",
            5,
            10,
            "required output exists, but no Jinja2 statement was detected",
            "Use a Jinja2 for loop in templates/vlans.j2 so additional YAML "
            "VLANs render automatically.",
        )
        return 5

    print_result(
        "Task 3 Jinja2 template",
        10,
        10,
        "template renders VLAN configuration correctly with Jinja2",
        "The template renders all supplied VLANs through a Jinja2 loop.",
    )
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
        print_result(
            "Task 4 device dictionary",
            0,
            10,
            f"device dictionary could not be imported: {type(exc).__name__}: {exc}",
            "Keep the settings-based connection values and add the Netmiko "
            "platform identifier required for Cisco Nexus NX-OS.",
        )
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
        print_result(
            "Task 4 device dictionary",
            0,
            10,
            f"missing or incorrect keys: {missing_or_wrong}",
            "Compare the dictionary with ConnectHandler requirements and "
            "Netmiko's supported-platform list. Preserve the host, username, "
            "password, and integer port mappings from settings.",
        )
        return 0

    print_result(
        "Task 4 device dictionary",
        10,
        10,
        "Netmiko device dictionary is correct",
        "The dictionary supplies all five values expected by ConnectHandler.",
    )
    return 10


def _exception_names(node: ast.expr | None) -> set[str]:
    if node is None:
        return set()
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, ast.Attribute):
        return {node.attr}
    if isinstance(node, ast.Tuple):
        names: set[str] = set()
        for item in node.elts:
            names.update(_exception_names(item))
        return names
    return set()


def _simulate_connection_failure(
    exception: Exception,
    expected_words: tuple[str, ...],
) -> tuple[bool, str]:
    module = importlib.import_module("scripts.apply_vlans")

    original_connect_handler = module.ConnectHandler
    original_renderer = module.render_vlan_config
    original_argv = sys.argv[:]

    def raise_connection_error(**_device: object) -> object:
        raise exception

    module.ConnectHandler = raise_connection_error
    module.render_vlan_config = lambda: "vlan 10\n  name IT"
    sys.argv = ["apply_vlans.py"]
    output = io.StringIO()

    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            module.main()
    except Exception as exc:
        return False, f"exception escaped from main(): {type(exc).__name__}: {exc}"
    finally:
        module.ConnectHandler = original_connect_handler
        module.render_vlan_config = original_renderer
        sys.argv = original_argv

    message = output.getvalue().lower()
    if not any(word in message for word in expected_words):
        return False, f"message must contain one of {expected_words}"
    return True, "exception handled with a clear message"


def grade_exception_handling() -> int:
    path = ROOT / "scripts/apply_vlans.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print_result(
            "Task 5 Netmiko exceptions",
            0,
            10,
            f"script could not be parsed: {type(exc).__name__}: {exc}",
            "Import and catch NetmikoAuthenticationException and "
            "NetmikoTimeoutException around the connection/session block.",
        )
        return 0

    handled: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            handled.update(_exception_names(node.type))

    checks = [
        (
            "NetmikoAuthenticationException",
            NetmikoAuthenticationException("simulated authentication failure"),
            ("authentication",),
        ),
        (
            "NetmikoTimeoutException",
            NetmikoTimeoutException("simulated connection timeout"),
            ("timeout", "timed out"),
        ),
    ]

    score = 0
    details = []
    for class_name, exception, words in checks:
        if class_name not in handled:
            details.append(f"{class_name} handler missing")
            continue

        passed, detail = _simulate_connection_failure(exception, words)
        if passed:
            score += 5
        details.append(f"{class_name}: {detail}")

    print_result(
        "Task 5 Netmiko exceptions",
        score,
        10,
        "; ".join(details),
        "Catch both specific Netmiko exceptions without letting either escape. "
        "Print 'authentication' for rejected credentials and 'timeout' or "
        "'timed out' when connection establishment times out.",
    )
    return score


def main() -> None:
    print("Project 1 Self-Grading")
    print("=" * 60)
    score = (
        grade_dependency()
        + grade_env()
        + grade_template()
        + grade_device_dictionary()
        + grade_exception_handling()
    )
    print("=" * 60)
    print(f"Project 1 score: {score}/50")
    incomplete = [result for result in RESULTS if result[1] < result[2]]
    if incomplete:
        print("\nIncomplete requirements:")
        for name, points, maximum, expected in incomplete:
            print(f"- {name}: missing {maximum - points} point(s). {expected}")
        print("Correct the listed requirements and run this grader again.")
    else:
        print("All locally gradable Project 1 requirements are complete.")
        print("The grader does not replace sandbox deployment verification.")


if __name__ == "__main__":
    main()
