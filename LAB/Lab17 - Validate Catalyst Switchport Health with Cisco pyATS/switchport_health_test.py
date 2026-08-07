#!/usr/bin/env python3
"""pyATS test that detects increasing Catalyst switchport health counters."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from pyats import aetest
from genie.metaparser.util.exceptions import SchemaEmptyParserError


PORT_NAME = re.compile(
    r"^(?:GigabitEthernet|TenGigabitEthernet|TwentyFiveGigE|"
    r"FortyGigabitEthernet|HundredGigE|Ethernet)"
)

# These paths follow the IOS XE Genie ShowInterfaces schema. More than one
# path is supplied only where IOS XE variants expose the same operational
# counter in different parser locations.
METRIC_PATHS = {
    "crc_errors": (("counters", "in_crc_errors"),),
    "interface_resets": (("counters", "out_interface_resets"),),
    "collisions": (("counters", "out_collision"),),
    "output_errors": (("counters", "out_errors"),),
    "output_drops": (
        ("queues", "total_output_drop"),
        ("counters", "out_drops"),
    ),
}


def integer_counter(value) -> int:
    """Normalize an integer or numeric string returned by a Genie parser."""

    if isinstance(value, bool):
        raise ValueError("Boolean is not a counter")
    if isinstance(value, int):
        return value
    return int(str(value).replace(",", "").strip())


def value_at_path(node: dict, path: tuple[str, ...]):
    """Return a nested value, or None when the structured path is absent."""

    current = node
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def extract_switchport_counters(parsed: dict) -> dict[str, dict[str, int]]:
    """Extract supported health counters for physical Ethernet interfaces."""

    results: dict[str, dict[str, int]] = {}
    interfaces = parsed.get("interfaces", parsed)
    if not isinstance(interfaces, dict):
        return results

    for interface, details in interfaces.items():
        if not PORT_NAME.match(interface) or not isinstance(details, dict):
            continue

        metrics: dict[str, int] = {}
        for metric, candidate_paths in METRIC_PATHS.items():
            for path in candidate_paths:
                value = value_at_path(details, path)
                if value is not None:
                    metrics[metric] = integer_counter(value)
                    break

        if metrics:
            results[interface] = metrics
    return results


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testbed):
        device = testbed.devices["catalyst"]
        device.connect(log_stdout=False)
        self.parent.parameters["device"] = device


class SwitchportHealthTest(aetest.Testcase):
    @aetest.setup
    def collect_baseline(self, device):
        try:
            parsed = device.parse("show interfaces")
        except SchemaEmptyParserError:
            self.failed("`show interfaces` returned no parseable data")

        baseline = extract_switchport_counters(parsed)
        if not baseline:
            self.failed(
                "No supported switchport health counters were found; "
                "inspect the Genie parser output and platform support"
            )
        self.parent.parameters["baseline"] = baseline

    @aetest.test
    def compare_samples(
        self,
        device,
        baseline,
        sample_interval,
        increase_threshold,
    ):
        time.sleep(sample_interval)
        current = extract_switchport_counters(device.parse("show interfaces"))
        rows = []
        offenders = []

        for interface, before_metrics in sorted(baseline.items()):
            if interface not in current:
                rows.append(
                    {
                        "interface": interface,
                        "metric": "all",
                        "baseline": before_metrics,
                        "current": None,
                        "delta": None,
                        "status": "interface-missing-from-second-sample",
                    }
                )
                offenders.append(f"{interface}:missing")
                continue

            for metric, before in sorted(before_metrics.items()):
                if metric not in current[interface]:
                    rows.append(
                        {
                            "interface": interface,
                            "metric": metric,
                            "baseline": before,
                            "current": None,
                            "delta": None,
                            "status": "counter-missing-from-second-sample",
                        }
                    )
                    offenders.append(f"{interface}:{metric}:missing")
                    continue

                after = current[interface][metric]
                delta = after - before
                status = "pass"
                if delta < 0:
                    status = "counter-reset"
                    offenders.append(f"{interface}:{metric}:reset")
                elif delta > increase_threshold:
                    status = "counter-increase"
                    offenders.append(f"{interface}:{metric}:+{delta}")

                rows.append(
                    {
                        "interface": interface,
                        "metric": metric,
                        "baseline": before,
                        "current": after,
                        "delta": delta,
                        "status": status,
                    }
                )

        artifact_dir = Path("artifacts")
        artifact_dir.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        report = artifact_dir / f"switchport_health_{timestamp}.json"
        report.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

        if offenders:
            self.failed(
                "Switchport health test failed for "
                + ", ".join(offenders)
                + f"; review {report}"
            )
        self.passed(
            "No monitored counter increase exceeded "
            f"{increase_threshold}; review {report}"
        )


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self, device):
        if device.is_connected():
            device.disconnect()
