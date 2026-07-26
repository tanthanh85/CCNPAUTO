#!/usr/bin/env python3
"""pyATS test that detects increasing CRC counters on Catalyst switch ports."""

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
CRC_KEYS = (
    "in_crc_errors",
    "input_crc",
    "crc_errors",
    "crc",
)


def integer_counter(value) -> int:
    """Normalize an integer or numeric string returned by a Genie parser."""

    if isinstance(value, bool):
        raise ValueError("Boolean is not a counter")
    if isinstance(value, int):
        return value
    return int(str(value).replace(",", "").strip())


def find_crc_counter(node):
    """Find a scalar CRC counter in a parser subtree."""

    if not isinstance(node, dict):
        return None
    for key in CRC_KEYS:
        if key in node and not isinstance(node[key], (dict, list)):
            return node[key]
    for key, value in node.items():
        if "crc" in str(key).lower() and not isinstance(value, (dict, list)):
            return value
    for value in node.values():
        candidate = find_crc_counter(value)
        if candidate is not None:
            return candidate
    return None


def extract_crc_counters(parsed: dict) -> dict[str, int]:
    """Return input CRC counters from parsed `show interfaces` output."""

    results = {}
    for interface, details in parsed.get("interfaces", {}).items():
        if not PORT_NAME.match(interface):
            continue
        value = find_crc_counter(details)
        if value is not None:
            results[interface] = integer_counter(value)
    return results


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testbed):
        device = testbed.devices["catalyst"]
        device.connect(log_stdout=False)
        self.parent.parameters["device"] = device


class CRCCounterTest(aetest.Testcase):
    @aetest.setup
    def collect_baseline(self, device):
        try:
            parsed = device.parse("show interfaces")
        except SchemaEmptyParserError:
            self.failed("`show interfaces` returned no parseable data")

        baseline = extract_crc_counters(parsed)
        if not baseline:
            self.failed(
                "No Ethernet CRC counters were found in the Genie result; "
                "inspect the parser output and platform support"
            )
        self.parent.parameters["baseline"] = baseline

    @aetest.test
    def compare_samples(
        self,
        device,
        baseline,
        sample_interval,
        crc_threshold,
    ):
        time.sleep(sample_interval)
        current = extract_crc_counters(device.parse("show interfaces"))
        rows = []
        offenders = []

        for interface, before in sorted(baseline.items()):
            if interface not in current:
                rows.append(
                    {
                        "interface": interface,
                        "baseline": before,
                        "current": None,
                        "delta": None,
                        "status": "missing-from-second-sample",
                    }
                )
                offenders.append(interface)
                continue

            after = current[interface]
            delta = after - before
            status = "pass"
            if delta < 0:
                status = "counter-reset"
                offenders.append(interface)
            elif delta > crc_threshold:
                status = "crc-increase"
                offenders.append(interface)

            rows.append(
                {
                    "interface": interface,
                    "baseline": before,
                    "current": after,
                    "delta": delta,
                    "status": status,
                }
            )

        artifact_dir = Path("artifacts")
        artifact_dir.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        report = artifact_dir / f"crc_results_{timestamp}.json"
        report.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

        if offenders:
            self.failed(
                "CRC test failed for: "
                + ", ".join(offenders)
                + f"; review {report}"
            )
        self.passed(f"No CRC increase exceeded {crc_threshold}; review {report}")


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self, device):
        if device.is_connected():
            device.disconnect()
