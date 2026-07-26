from __future__ import annotations

import logging
import re


logger = logging.getLogger(__name__)


def parse_loopbacks(config):
    logger.debug("Parsing loopback configuration characters=%d", len(config))
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
    logger.info("Parsed %d loopback interface(s) from observed configuration", len(result))
    logger.debug("Parsed loopback configuration=%s", result)
    return result


def parse_ospf_networks(config):
    networks = sorted(set(re.findall(r"^\s*network\s+(\d+\.\d+\.\d+\.\d+)\s+0\.0\.0\.0\s+area\s+0\s*$", config, re.M)))
    logger.info("Parsed %d OSPF area 0 host network statement(s)", len(networks))
    logger.debug("Parsed OSPF networks=%s", networks)
    return networks


def build_drift_report(intent, interface_config, ospf_config):
    logger.info("Building drift report intended_records=%d", len(intent))
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
    report = {
        "compliant": compliant,
        "expected_count": len(expected),
        "observed_count": len(observed),
        "missing_interfaces": sorted(missing),
        "mismatched_interfaces": mismatched,
        "missing_ospf_networks": sorted(ospf_missing),
        "unmanaged_loopbacks": unmanaged,
    }
    logger.info(
        "Drift report complete compliant=%s expected=%d observed=%d "
        "missing=%d mismatched=%d ospf_missing=%d unmanaged=%d",
        report["compliant"],
        report["expected_count"],
        report["observed_count"],
        len(report["missing_interfaces"]),
        len(report["mismatched_interfaces"]),
        len(report["missing_ospf_networks"]),
        len(report["unmanaged_loopbacks"]),
    )
    logger.debug("Drift report=%s", report)
    return report


class FilterModule:
    def filters(self):
        return {
            "parse_loopbacks": parse_loopbacks,
            "parse_ospf_networks": parse_ospf_networks,
            "build_drift_report": build_drift_report,
        }
