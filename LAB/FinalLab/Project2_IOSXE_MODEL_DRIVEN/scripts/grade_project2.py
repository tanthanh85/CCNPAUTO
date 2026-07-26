from __future__ import annotations

import ast
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


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


def grade_static_route_template() -> int:
    template_path = ROOT / "templates/static_routes.xml.j2"
    template_text = template_path.read_text(encoding="utf-8")
    if "<config" not in template_text:
        print_result(
            "Task 1 NETCONF payload",
            0,
            15,
            "template is missing the required <config> root element",
            "Keep the supplied NETCONF <config> root and place Cisco-IOS-XE-native "
            "static-route XML inside the existing Jinja2 loop.",
        )
        return 0

    try:
        data = yaml.safe_load((ROOT / "data/static_routes.yaml").read_text(encoding="utf-8"))
        env = Environment(
            loader=FileSystemLoader(ROOT / "templates"),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        rendered = env.get_template("static_routes.xml.j2").render(static_routes=data["static_routes"])
        ET.fromstring(rendered)
    except Exception as exc:
        print_result(
            "Task 1 NETCONF payload",
            0,
            15,
            f"rendered XML failed validation: {type(exc).__name__}: {exc}",
            "The rendered result must be well-formed XML with IOS XE Native "
            "namespaces and one static-route entry per YAML record.",
        )
        return 0

    route = data["static_routes"][0]
    expected_fragments = [route["prefix"], route["mask"], route["next_hop"]]
    missing = [item for item in expected_fragments if item not in rendered]
    if missing:
        print_result(
            "Task 1 NETCONF payload",
            8,
            15,
            f"XML is valid but is missing route values: {missing}",
            "Reference route.prefix, route.mask, and route.next_hop inside "
            "the Cisco IOS XE Native static-route hierarchy.",
        )
        return 8

    if "{%" not in template_text:
        print_result(
            "Task 1 NETCONF payload",
            12,
            15,
            "XML works, but the required Jinja2 statement was not detected",
            "Use the supplied Jinja2 for loop so every route in "
            "data/static_routes.yaml renders automatically.",
        )
        return 12

    print_result(
        "Task 1 NETCONF payload",
        15,
        15,
        "static-route template renders valid XML with route values and Jinja2",
        "Valid XML, Cisco IOS XE Native structure, all required values, and "
        "a Jinja2 loop are present.",
    )
    return 15


def grade_vault_function() -> int:
    path = ROOT / "src/vault_credentials.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        print_result(
            "Task 2 Vault credentials",
            0,
            20,
            f"Vault module could not be parsed: {type(exc).__name__}: {exc}",
            "Implement get_iosxe_credentials_from_vault() as valid Python.",
        )
        return 0

    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "get_iosxe_credentials_from_vault"
        ),
        None,
    )
    if function is None:
        print_result(
            "Task 2 Vault credentials",
            0,
            20,
            "get_iosxe_credentials_from_vault() was not found",
            "Keep and complete the supplied function with hvac KV v2 retrieval.",
        )
        return 0

    score = 0
    details = []

    placeholder = any(
        isinstance(node, ast.Pass)
        or (
            isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and node.exc.func.id == "NotImplementedError"
        )
        for node in ast.walk(function)
    )
    if not placeholder:
        score += 5
        details.append("placeholder removed")
    else:
        details.append("placeholder remains")

    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
    ]
    has_hvac_client = any(
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "hvac"
        and call.func.attr == "Client"
        for call in calls
    )
    if has_hvac_client:
        score += 5
        details.append("executed hvac.Client call detected")
    else:
        details.append("executed hvac.Client call not detected")

    has_kv_v2_read = any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "read_secret_version"
        for call in calls
    )
    if has_kv_v2_read:
        score += 5
        details.append("executed KV v2 read detected")
    else:
        details.append("executed KV v2 read not detected")

    has_credential_return = any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Dict)
        and {
            key.value
            for key in node.value.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        >= {"username", "password"}
        for node in ast.walk(function)
    )
    if has_credential_return:
        score += 5
        details.append("username/password dictionary return detected")
    else:
        details.append("username/password dictionary return not detected")

    print_result(
        "Task 2 Vault credentials",
        score,
        20,
        "; ".join(details),
        "Remove the placeholder, create an authenticated hvac.Client, read "
        "VAULT_SECRET_PATH from KV v2, extract data.data, validate username "
        "and password, and return both values in a dictionary.",
    )
    return score


def extract_constant(tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value
    return ""


def grade_restconf_uris() -> int:
    path = ROOT / "src/restconf_monitor.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        print_result(
            "Task 3 RESTCONF monitoring URIs",
            0,
            15,
            f"monitor module could not be parsed: {type(exc).__name__}: {exc}",
            "Define three quoted resource paths beginning with '/' in "
            "CPU_URI, MEMORY_URI, and INTERFACE_GIG1_URI.",
        )
        return 0
    constants = {
        "CPU_URI": extract_constant(tree, "CPU_URI"),
        "MEMORY_URI": extract_constant(tree, "MEMORY_URI"),
        "INTERFACE_GIG1_URI": extract_constant(tree, "INTERFACE_GIG1_URI"),
    }

    weights = {"CPU_URI": 5, "MEMORY_URI": 5, "INTERFACE_GIG1_URI": 5}
    points = 0
    detail = []
    for name, value in constants.items():
        valid = (
            value.startswith("/")
            and "/restconf/data/" not in value
            and "TODO" not in value.upper()
            and "REPLACE" not in value.upper()
        )
        if valid:
            points += weights[name]
            detail.append(f"{name} completed (+{weights[name]})")
        else:
            detail.append(f"{name} missing or malformed (+0/{weights[name]})")

    print_result(
        "Task 3 RESTCONF monitoring URIs",
        points,
        15,
        "; ".join(detail),
        "Use Yangsuite-validated device resource paths only. Each constant "
        "must begin with '/', omit scheme/host and /restconf/data, and identify "
        "CPU, memory, or the GigabitEthernet1 list entry respectively.",
    )
    return points


def main() -> None:
    print("Project 2 Self-Grading")
    print("=" * 60)
    score = grade_static_route_template() + grade_vault_function() + grade_restconf_uris()
    print("=" * 60)
    print(f"Project 2 score: {score}/50")
    incomplete = [result for result in RESULTS if result[1] < result[2]]
    if incomplete:
        print("\nIncomplete requirements:")
        for name, points, maximum, expected in incomplete:
            print(f"- {name}: missing {maximum - points} point(s). {expected}")
        print("Correct the listed requirements and run this grader again.")
    else:
        print("All locally gradable Project 2 requirements are complete.")
        print("The grader does not replace NETCONF, Vault, or portal verification.")


if __name__ == "__main__":
    main()
