from __future__ import annotations

import re


def parse_loopbacks(config):
    result = {}
    current = None
    for raw in config.splitlines():
        line = raw.strip()
        match = re.match(r"interface (Loopback\d+)$", line)
        if match:
            current = match.group(1)
            result[current] = {"description": "", "ipv4": "", "enabled": True}
            continue
        if current is None:
            continue
        if line.startswith("interface ") or line == "!":
            current = None
        elif line.startswith("description "):
            result[current]["description"] = line.removeprefix("description ")
        elif line.startswith("ip address "):
            result[current]["ipv4"] = line.split()[2]
        elif line == "shutdown":
            result[current]["enabled"] = False
    return result


def parse_ospf_networks(config):
    return sorted(set(re.findall(r"^\s*network\s+(\d+\.\d+\.\d+\.\d+)\s+0\.0\.0\.0\s+area\s+0\s*$", config, re.M)))


def build_drift_report(intent, interface_config, ospf_config):
    observed = parse_loopbacks(interface_config)
    expected = {item["name"]: item for item in intent}
    missing, mismatched, ospf_missing = [], [], []
    for name, item in expected.items():
        if name not in observed:
            missing.append(name)
            continue
        actual = observed[name]
        differences = {}
        expected_values = {
            "ipv4": item["ipv4"],
            "enabled": item["enabled"],
            "description": item.get("description") or "NETBOX_MANAGED",
        }
        for field, expected_value in expected_values.items():
            if actual[field] != expected_value:
                differences[field] = {"expected": expected_value, "observed": actual[field]}
        if differences:
            mismatched.append({"name": name, "differences": differences})
        if item["ipv4"] not in parse_ospf_networks(ospf_config):
            ospf_missing.append(item["ipv4"])
    unmanaged = sorted(set(observed) - set(expected))
    compliant = not any((missing, mismatched, ospf_missing, unmanaged))
    return {
        "compliant": compliant,
        "expected_count": len(expected),
        "observed_count": len(observed),
        "missing_interfaces": sorted(missing),
        "mismatched_interfaces": mismatched,
        "missing_ospf_networks": sorted(ospf_missing),
        "unmanaged_loopbacks": unmanaged,
    }


class FilterModule:
    def filters(self):
        return {
            "parse_loopbacks": parse_loopbacks,
            "parse_ospf_networks": parse_ospf_networks,
            "build_drift_report": build_drift_report,
        }
