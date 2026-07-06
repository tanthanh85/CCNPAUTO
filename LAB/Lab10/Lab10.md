# Lab 10: Add Application Logging and Observability

## Lab Introduction

Network configuration is only half of an automation system. Operators must also know who initiated a run, which tasks executed, how long they took, what changed, and where a failure occurred. Lab 10 adds structured JSON Lines audit events to every Ansible job, preserves them as GitLab artifacts, publishes nonsecret task metrics to InfluxDB, and visualizes pipeline behavior in Grafana.

## Learning Objectives

- Separate human-readable job output, structured audit events, and metrics.
- Add correlation fields such as pipeline ID and job name.
- Prevent secret-bearing results from entering logs.
- Retain artifacts even when a job fails.
- Publish duration, status, and change metrics to InfluxDB.
- Build Grafana views for failures, changes, and execution time.

## Task 1: Add the Logging Components

```bash
cd ~/ccnpauto-workspace/network_automation_project
git switch main && git pull --ff-only
git switch -c feature/automation-observability
LAB10_FILES="/path/to/CCNPAUTO/LAB/Lab10"
mkdir -p callback_plugins scripts
cp "$LAB10_FILES/callback_plugins/json_audit.py" callback_plugins/
cp "$LAB10_FILES/scripts/publish_audit_metrics.py" scripts/
```

Add these settings under the existing `[defaults]` section of `ansible.cfg`:

```ini
callback_plugins = ./callback_plugins
callbacks_enabled = json_audit
```

The callback records metadata, not module return bodies. Tasks marked `no_log` are identified as protected, while their arguments and results remain absent. A log system must not become a second secret database.

## Task 2: Test Structured Logging Locally

```bash
mkdir -p artifacts
export ANSIBLE_AUDIT_LOG="artifacts/local-audit.jsonl"
ansible-playbook playbooks/validate.yml
python -m json.tool < <(head -n 1 artifacts/local-audit.jsonl)
```

Each line is an independent JSON document. This makes partial files recoverable and easy for log agents to stream. Inspect the file and confirm it contains timestamps, task names, hosts, status, duration, pipeline correlation, and changed state—but no tokens or passwords.

## Task 3: Extend the Pipeline

Add an `observe` stage after `test`. Before each Ansible invocation, set a unique audit filename:

```yaml
variables:
  ANSIBLE_AUDIT_LOG: "artifacts/${CI_JOB_NAME}.jsonl"
```

Add the supplied `observe-automation` job from `pipeline-observe-job.yml`. Configure these protected GitLab variables:

| Variable | Value |
|---|---|
| `INFLUX_URL` | `http://127.0.0.1:8086` |
| `INFLUX_ORG` | Lab 1 organization, normally `ccnpauto` |
| `INFLUX_BUCKET` | Lab 1 bucket, normally `workstation` |
| `INFLUX_TOKEN` | Lab 1 token; masked and protected |

The shell Runner reaches the workstation-bound InfluxDB endpoint directly. The observe job downloads artifacts from earlier stages, converts task events to Influx line protocol, and writes only operational metadata.

## Task 4: Build the Grafana Views

Open `http://127.0.0.1:3000`, select the InfluxDB data source, and create a dashboard named **Network Automation Pipeline**. Useful panels include:

- Task count grouped by `status`
- Failed and unreachable task count over time
- Mean `duration_seconds` grouped by `job_name`
- Changed task count grouped by pipeline
- Longest task durations in the selected time range

A representative Flux query is:

```flux
from(bucket: "workstation")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "automation_task")
  |> filter(fn: (r) => r._field == "duration_seconds")
  |> group(columns: ["job_name"])
  |> mean()
```

## Task 5: Trigger and Diagnose a Failure

Create a deliberately incomplete tagged loopback in NetBox, then manually trigger the pipeline if the IP-address event has not fired. Validation must fail, deployment must not run, and the audit artifact must show the failed task without exposing the NetBox token. Correct the object, trigger again, and compare the two pipeline IDs in Grafana.

## Task 6: Commit and Exercise the Event Flow

```bash
git add ansible.cfg callback_plugins scripts .gitlab-ci.yml
git commit -m "Add structured audit logging and pipeline metrics"
git push -u origin feature/automation-observability
```

After merge, create a complete loopback in NetBox. Confirm the webhook-triggered pipeline configures and tests it, uploads JSONL and text artifacts, and publishes metrics.

## Key Takeaways

- Logs explain individual events; metrics reveal trends across many runs.
- Correlation identifiers connect NetBox changes, GitLab jobs, and device outcomes.
- `no_log` and metadata-only callbacks reduce credential exposure.
- Failed pipelines need artifacts even more than successful pipelines do.
- A dashboard supports diagnosis but does not replace retained audit evidence.

Lab 11 packages the Ansible dependencies and collections into a consistent containerized runtime.

## References

- [Ansible callback plugins](https://docs.ansible.com/ansible/latest/plugins/callback.html)
- [InfluxDB write API](https://docs.influxdata.com/influxdb/v2/api-guide/client-libraries/)
- [Grafana dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
