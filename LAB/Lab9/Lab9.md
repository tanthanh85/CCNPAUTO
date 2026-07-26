# Lab 9: Add API Resilience to your network automation project

## Lab Introduction

The Lab 8 pipeline assumes that NetBox and Vault respond immediately. Real APIs occasionally time out, reset a connection, return `429 Too Many Requests`, or produce a temporary `5xx` response. This lab keeps the same NetBox-triggered workflow but adds bounded retry behavior to the Ansible project. Recoverable failures use exponential backoff with jitter, `429` responses honor `Retry-After`, and unrecoverable `4xx` responses stop immediately.

## Learning Objectives

- Distinguish transient, rate-limit, and unrecoverable API failures.
- Apply connection and read timeouts.
- Use bounded exponential backoff rather than an infinite retry loop.
- Respect `Retry-After` and avoid synchronized retry storms with jitter.
- Protect authorization headers and diagnostic logs.
- Test retry helper behavior before deployment.

## Task 1: Extend the Existing Repository

Start and verify the services used by the resilient API and pipeline tests:

```bash
cd "$HOME/lab-services/netbox-docker"
docker compose up -d
vault status
sudo systemctl start gitlab-runner
sudo gitlab-runner verify
```

TIG and local Yangsuite are not required and may remain stopped.

```bash
cd ~/ccnpauto-workspace/network_automation_project
git switch main && git pull --ff-only
git switch -c feature/api-resilience
mkdir -p library tests tasks
```

Using the VS Code Explorer, copy and paste `library/resilient_http.py`, `tests/test_resilient_http_helpers.py`, `tasks/load_intent.yml`, and `.gitlab-ci.yml` from `CCNPAUTO/LAB/Lab9/` into the matching project locations. Open the existing `requirements.txt` and add `pytest>=8,<9` only if it is not already present.

Ansible executes a custom module from a temporary module environment, so `resilient_http.py` contains a small dedicated logger rather than importing the project package. It consumes the same logging controls and records attempts, status codes, elapsed time, retry classification, `Retry-After`, backoff, and the final outcome. Request headers are declared `no_log` and are never written.

The custom Ansible module uses `requests.get()` with a ten-second timeout and defaults `verify_tls` to `false` for the isolated lab services. Statuses `429`, `500`, `502`, `503`, and `504`, plus transport exceptions, consume the retry budget. Other HTTP errors are classified as unrecoverable. The module returns only status and attempt metadata; authorization headers are declared `no_log`.

## Task 2: Run Automated Tests

```bash
source ~/.venvs/ccnpauto/bin/activate
python -m pip install -r requirements.txt
pytest -q tests/test_resilient_http_helpers.py
ansible-playbook --syntax-check playbooks/validate.yml
```

The helper tests validate both forms of `Retry-After`: seconds and an HTTP date. The pipeline runs them before reading NetBox or changing IOS XE.

## Task 3: Observe Recoverable and Unrecoverable Failures

With file logging enabled, compare a retryable failure and an unrecoverable failure in `logs/resilient_http_*.log`. The first should show its attempt and wait decisions; the second should stop immediately with an unrecoverable category. Authorization headers and tokens must not appear.

Stop NetBox briefly and run validation. The module should retry transport failures and then report `retry_exhausted`; it must not hang indefinitely.

```bash
cd ~/lab-services/netbox-docker
docker compose stop netbox
cd ~/ccnpauto-workspace/network_automation_project
time ansible-playbook playbooks/validate.yml
cd ~/lab-services/netbox-docker
docker compose up -d
```

Next, temporarily export an invalid NetBox token. A `401` or `403` is not repaired by waiting, so the module should report `unrecoverable_http`. Restore the valid token without recording it in shell output.

## Task 4: Preserve the Event-Driven Workflow

Commit, push, review, and merge while the sandbox and local services are ready:

```bash
git add .gitlab-ci.yml requirements.txt library tests tasks/load_intent.yml
git commit -m "Add bounded API retries and backoff"
git push -u origin feature/api-resilience
```

Create a new complete loopback in NetBox. The webhook still triggers GitLab.com; the Runner now uses the resilient module whenever it retrieves interface intent. Inspect `resilience-tests.log` and the Ansible artifacts.

## Failure Policy

| Condition | Action |
|---|---|
| Timeout or connection reset | Retry within the bounded budget |
| HTTP 429 | Wait for `Retry-After`, then retry |
| HTTP 5xx | Exponential backoff with jitter |
| HTTP 400, 401, 403, 404 | Stop and correct request, identity, or URL |
| Invalid JSON | Stop; do not configure from an ambiguous response |
| Retry budget exhausted | Fail the pipeline and preserve diagnostic metadata |

## Finish on the Latest Main Branch

After the resilient pipeline succeeds and GitLab shows the merge request as
**Merged**, synchronize the local clone:

```bash
cd ~/ccnpauto-workspace/network_automation_project
git switch main
git pull --ff-only
git status
```

Confirm that `git status` reports `main` is up to date with `origin/main` and
that the working tree is clean. Begin the next project lab from this branch,
not from the completed feature branch.

## Key Takeaways

- Retries are appropriate only for failures likely to recover without changing the request.
- Timeouts, retry limits, backoff, and jitter protect both client and API.
- Authentication and validation errors require human or code correction.
- A failed intent read must prevent all device changes.

Lab 10 turns Ansible execution events into structured audit logs and observability metrics.

## References

- [HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [Ansible custom modules](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)
- [Requests timeouts](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts)
