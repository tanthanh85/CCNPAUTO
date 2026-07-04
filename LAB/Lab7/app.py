#!/usr/bin/env python3
"""Simulated network automation workflow with operational and audit logging."""

import argparse
import logging
import os
import time
import uuid
from pathlib import Path

import yaml

from src.logging_config import configure_logging


class AuthenticationFailure(RuntimeError):
    pass


class DeviceTimeout(RuntimeError):
    pass


class SimulatedDeviceClient:
    def __init__(self, hostname, scenario):
        self.hostname = hostname
        self.scenario = scenario

    def connect(self):
        if self.scenario == "auth" and self.hostname == "branch-r1":
            raise AuthenticationFailure("Device rejected the supplied identity")
        if self.scenario == "timeout" and self.hostname == "branch-r1":
            raise DeviceTimeout("Connection timed out after 10 seconds")
        time.sleep(0.05)

    def configure(self, commands):
        if self.scenario == "partial" and self.hostname == "branch-r2":
            raise RuntimeError("Device rejected command 2: invalid input")
        time.sleep(0.05)
        return len(commands)

    def verify(self):
        if self.scenario == "verify" and self.hostname == "branch-r2":
            return False
        return True


class ChangeWorkflow:
    def __init__(self, plan, scenario, actor, correlation_id, logger, audit_logger):
        self.plan = plan
        self.scenario = scenario
        self.actor = actor
        self.correlation_id = correlation_id
        self.logger = logger
        self.audit = audit_logger

    def context(self, **extra):
        return {
            "correlation_id": self.correlation_id,
            "change_id": self.plan["change_id"],
            "actor": self.actor,
            **extra,
        }

    def run(self):
        failures = 0
        started = time.monotonic()
        self.logger.info(
            "Network change workflow started",
            extra=self.context(event_type="workflow_started", command_count=len(self.plan["commands"])),
        )

        for device in self.plan["devices"]:
            device_started = time.monotonic()
            hostname = device["hostname"]
            details = self.context(device=hostname, management_ip=device["management_ip"])
            client = SimulatedDeviceClient(hostname, self.scenario)

            try:
                self.logger.info("Connecting to device", extra={**details, "event_type": "connection_started"})
                client.connect()
                self.logger.info("Device connection established", extra={**details, "event_type": "connection_succeeded"})

                applied = client.configure(self.plan["commands"])
                self.audit.info(
                    "Approved network change submitted",
                    extra={**details, "event_type": "configuration_submitted", "command_count": applied, "outcome": "submitted"},
                )

                if not client.verify():
                    raise RuntimeError("Post-change verification did not match intended state")

                duration = round((time.monotonic() - device_started) * 1000, 2)
                self.logger.info(
                    "Device change verified",
                    extra={**details, "event_type": "verification_succeeded", "duration_ms": duration, "outcome": "success"},
                )
                self.audit.info(
                    "Network change completed",
                    extra={**details, "event_type": "change_completed", "duration_ms": duration, "outcome": "success"},
                )
            except Exception as error:
                failures += 1
                duration = round((time.monotonic() - device_started) * 1000, 2)
                self.logger.exception(
                    "Device workflow failed",
                    extra={**details, "event_type": "device_failed", "duration_ms": duration, "outcome": "failure", "error_type": type(error).__name__},
                )
                self.audit.error(
                    "Network change failed",
                    extra={**details, "event_type": "change_failed", "duration_ms": duration, "outcome": "failure", "error_type": type(error).__name__},
                )

        total_duration = round((time.monotonic() - started) * 1000, 2)
        outcome = "success" if failures == 0 else "partial_failure"
        self.logger.info(
            "Network change workflow completed",
            extra=self.context(event_type="workflow_completed", duration_ms=total_duration, outcome=outcome),
        )
        return 0 if failures == 0 else 1


def load_plan(path):
    plan = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    required = {"change_id", "description", "devices", "commands"}
    if set(plan) != required:
        raise ValueError(f"Plan must contain exactly: {sorted(required)}")
    if not plan["devices"] or not plan["commands"]:
        raise ValueError("Plan must contain devices and commands")
    return plan


parser = argparse.ArgumentParser()
parser.add_argument("--plan", default="data/change_plan.yaml")
parser.add_argument("--scenario", choices=["success", "auth", "timeout", "partial", "verify"], default="success")
parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
parser.add_argument("--max-log-bytes", type=int, default=1_000_000)
arguments = parser.parse_args()

try:
    app_logger, audit_logger = configure_logging(arguments.log_level, arguments.max_log_bytes)
    plan = load_plan(arguments.plan)
    actor = os.getenv("AUTOMATION_ACTOR", os.getenv("USER", "unknown"))
    correlation_id = str(uuid.uuid4())
    workflow = ChangeWorkflow(plan, arguments.scenario, actor, correlation_id, app_logger, audit_logger)
    raise SystemExit(workflow.run())
except (OSError, ValueError, yaml.YAMLError) as error:
    logging.getLogger("network_automation").exception("Application initialization failed")
    print(f"Application initialization failed: {error}")
    raise SystemExit(2)
