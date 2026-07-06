from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "json_audit"
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()
        self.path = Path(os.getenv("ANSIBLE_AUDIT_LOG", "artifacts/ansible-audit.jsonl"))
        self.started = {}

    def _write(self, event, **fields):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "pipeline_id": os.getenv("CI_PIPELINE_ID", "local"),
            "job_name": os.getenv("CI_JOB_NAME", "local"),
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    def v2_runner_on_start(self, host, task):
        self.started[str(task._uuid)] = time.monotonic()

    def _result(self, result, status):
        task = result._task
        raw = result._result
        started = self.started.pop(str(task._uuid), time.monotonic())
        self._write(
            "task_result", host=result._host.get_name(), task=task.get_name(),
            status=status, changed=bool(raw.get("changed", False)),
            duration_seconds=round(time.monotonic() - started, 4),
            protected=bool(getattr(task, "no_log", False)),
        )

    def v2_runner_on_ok(self, result):
        self._result(result, "ok")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._result(result, "failed")

    def v2_runner_on_unreachable(self, result):
        self._result(result, "unreachable")

    def v2_runner_on_skipped(self, result):
        self._result(result, "skipped")

    def v2_playbook_on_stats(self, stats):
        for host in sorted(stats.processed):
            summary = stats.summarize(host)
            self._write("playbook_summary", host=host, **summary)
