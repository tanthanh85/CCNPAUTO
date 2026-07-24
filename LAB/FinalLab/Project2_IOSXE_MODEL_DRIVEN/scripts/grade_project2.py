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


def print_result(name: str, points: int, maximum: int, detail: str) -> None:
    print(f"{name}: {points}/{maximum} - {detail}")


def grade_static_route_template() -> int:
    template_path = ROOT / "templates/static_routes.xml.j2"
    template_text = template_path.read_text(encoding="utf-8")
    if "<config" not in template_text:
        print_result("Task 1 NETCONF payload", 0, 20, "template is missing the required <config> root element")
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
        print_result("Task 1 NETCONF payload", 0, 20, f"rendered XML failed validation: {exc}")
        return 0

    route = data["static_routes"][0]
    expected_fragments = [route["prefix"], route["mask"], route["next_hop"]]
    missing = [item for item in expected_fragments if item not in rendered]
    if missing:
        print_result("Task 1 NETCONF payload", 10, 20, f"XML is valid but missing route values: {missing}")
        return 10

    if "{%" not in template_text:
        print_result("Task 1 NETCONF payload", 15, 20, "XML works, but the required Jinja2 for loop was not detected")
        return 15

    print_result("Task 1 NETCONF payload", 20, 20, "static-route XML template renders valid route payload")
    return 20


def grade_vault_function() -> int:
    path = ROOT / "src/vault_credentials.py"
    text = path.read_text(encoding="utf-8")
    score = 0
    details = []

    if "NotImplementedError" not in text and "pass" not in text:
        score += 10
        details.append("placeholder removed")
    else:
        details.append("placeholder remains")

    if "hvac.Client" in text:
        score += 10
        details.append("hvac client detected")
    else:
        details.append("hvac client not detected")

    if "read_secret_version" in text or "kv.v2" in text:
        score += 5
        details.append("KV v2 read detected")
    else:
        details.append("KV v2 read not detected")

    if "username" in text and "password" in text and "return" in text:
        score += 5
        details.append("username/password return detected")
    else:
        details.append("username/password return not detected")

    print_result("Task 2 Vault credentials", score, 30, "; ".join(details))
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
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constants = {
        "CPU_URI": extract_constant(tree, "CPU_URI"),
        "MEMORY_URI": extract_constant(tree, "MEMORY_URI"),
        "INTERFACE_GIG1_URI": extract_constant(tree, "INTERFACE_GIG1_URI"),
    }

    points = 0
    detail = []
    for name, value in constants.items():
        if value and value.startswith("/") and "TODO" not in value and "REPLACE" not in value:
            points += 20 // 3
            detail.append(f"{name} completed")
        else:
            detail.append(f"{name} missing")

    if all(value and value.startswith("/") for value in constants.values()):
        points = 20

    print_result("Task 3 RESTCONF monitoring URIs", points, 20, "; ".join(detail))
    return points


def main() -> None:
    print("Project 2 Self-Grading")
    print("=" * 70)
    score = grade_static_route_template() + grade_vault_function() + grade_restconf_uris()
    print("=" * 70)
    print(f"Project 2 score: {score}/70")


if __name__ == "__main__":
    main()
