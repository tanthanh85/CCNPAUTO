# Lab 9: Containerize the Automation Runtime

## Lab Introduction

The pipeline currently installs Python packages and Ansible collections during each run. That approach is transparent but slow, and a dependency published tomorrow could behave differently from the one tested today. Lab 9 packages the automation runtime into a versioned Docker image. The repository remains mounted at runtime, while Ansible, Python dependencies, and collections come from the immutable image.

## Learning Objectives

- Distinguish application source from its execution environment.
- Build a non-root Ansible runtime image.
- Pin runtime dependencies and inspect image identity.
- Pass only approved environment variables into a container.
- Reach local NetBox, Vault, and VPN routes using host networking.
- Preserve the NetBox-triggered GitLab workflow and artifacts.

## Task 1: Add the Container Files

Verify Docker, NetBox, Vault, and the Runner before building the runtime:

```bash
docker version
cd "$HOME/lab-services/netbox-docker"
docker compose up -d
vault status
sudo systemctl start gitlab-runner
sudo gitlab-runner verify
```

Container jobs use `--network host`, while the shell Runner already executes in the workstation network namespace. Stop local Yangsuite because this lab does not use it.

```bash
cd ~/ccnpauto-workspace/network_automation_project
git switch main && git pull --ff-only
git switch -c feature/container-runtime
mkdir -p ci
chmod +x ci/run_playbook_container.sh
```

Using the VS Code Explorer, copy and paste `Dockerfile`, `.dockerignore`, and `.gitlab-ci.yml` from `CCNPAUTO/LAB/Lab9/` into the project root. Copy and paste `ci/run_playbook_container.sh` into the project `ci/` folder.

The image contains tools, not credentials or project source. `.dockerignore` prevents local artifacts, virtual environments, keys, and `.env` files from entering the build context.

The wrapper passes only approved logging controls and bind-mounts the
repository at `/workspace`. It also creates a temporary host directory,
mounts it at `/home/runtime`, and sets `HOME`, `ANSIBLE_LOCAL_TEMP`, and the
XDG cache paths to writable locations inside that directory. It also passes
`USER`, `LOGNAME`, and `USERNAME`. This is required because the container runs
with the Runner's numeric UID rather than the image's original UID, and that
host UID does not normally have an entry in the image's `/etc/passwd`.
Without the explicit runtime home, Ansible can try to create
`/.ansible/tmp` and fail with `Permission denied`. Without the username
variables, Python's `getpass.getuser()` can fail with `No username set in the
environment`. The wrapper removes the temporary directory when the job exits.

Python processes create unique files in `/workspace/logs`, where the Runner
can retain them after the container exits. No diagnostic log is baked into
the image.

## Task 2: Build and Inspect the Image

```bash
docker build --pull -t network-automation-runtime:lab9 .
docker run --rm --network host network-automation-runtime:lab9 --version
docker run --rm --network host --entrypoint id network-automation-runtime:lab9
docker history network-automation-runtime:lab9
```

The process should run as UID 10001 rather than root. Review `docker history` and confirm no secret was passed through an `ARG`, `ENV`, or copied file.

## Task 3: Test Locally

Set `CI_PROJECT_DIR` for the helper script and reuse the environment variables from Lab 8:

```bash
export CI_PROJECT_DIR="$PWD"
export AUTOMATION_IMAGE="network-automation-runtime:lab9"
export CI_PIPELINE_ID="local-lab9"
export CI_JOB_NAME="local-validation"
export ANSIBLE_AUDIT_LOG="artifacts/local-container.jsonl"
bash ci/run_playbook_container.sh playbooks/validate.yml artifacts/local-container.log
```

`--network host` is deliberate in this single-host lab: `127.0.0.1` inside the container reaches workstation services and the container shares VPN routes. This reduces isolation and is not a universal production recommendation. A production Runner should use controlled networks and explicit service endpoints.

After the container exits, inspect `artifacts/` and `logs/` on the host. Their ownership should match the learner or Runner account. A second execution with file logging enabled must create additional timestamped files rather than overwrite the first run.

## Task 4: Understand Secret and SSH Handling

The wrapper passes a fixed allowlist of environment-variable names. It never uses `--env-file` because that can expose unrelated workstation values. GitLab masks protected variables in job output, while Ansible `no_log` protects secret-bearing tasks.

The wrapper copies the current account's public host-key database to a
temporary read-only system `known_hosts` mount, then removes the copy when the
container exits. If the file does not yet exist, the wrapper supplies an empty
file; the course `ansible.cfg` already uses
`host_key_checking = False` for the controlled sandbox. It also runs the
container with the Runner's numeric UID and GID so artifacts written into the
bind-mounted project remain owned by the Runner. Never bake a changing
sandbox host key or a private SSH key into the image.

## Task 5: Run the Containerized Pipeline

The build job creates a commit-specific local image. Subsequent jobs on the same protected shell Runner use that exact tag. The source repository is mounted at `/workspace`, so the image does not need rebuilding for a playbook-only comparison outside CI; however, the pipeline deliberately builds per commit to produce clear provenance.

The supplied pipeline contains four stages: `build`, `validate`, `deploy`, and
`test`. The build stage creates the image and records its identity. The other
three stages execute the existing Ansible playbooks through the container
wrapper. This keeps the lab focused on runtime consistency; no separate
monitoring service is required.

```bash
git add Dockerfile .dockerignore ci .gitlab-ci.yml
git commit -m "Run network automation in a containerized runtime"
git push -u origin feature/container-runtime
```

Merge only when NetBox, Vault, VPN, and the sandbox are ready. Create a new loopback in NetBox and confirm the webhook triggers build, validate, deploy, and test stages. Download `container-build.log`, `image-identity.log`, Ansible logs, and JSONL audit artifacts.

## Operational Considerations

- A local image survives only on the Runner that built it; multiple Runners require a registry.
- A production image should be scanned, signed, assigned a digest, and promoted through environments.
- Pinning packages improves reproducibility but also creates an obligation to rebuild for security fixes.
- Mounting the Docker socket or using host networking grants significant access and requires a trusted protected Runner.
- The image must never contain Vault tokens, NetBox tokens, device passwords, or private keys.

If a job reports `Unable to create local directories '/.ansible/tmp'`, verify
that the project contains the current `ci/run_playbook_container.sh`. The
Docker command must mount a temporary directory at `/home/runtime` and set
`HOME=/home/runtime`. Rebuild the image after changing the Dockerfile so that
the required collections are installed under
`/usr/share/ansible/collections`.

If the next error is `No username set in the environment` or
`getpwuid(): uid not found`, the pipeline is still using an earlier wrapper.
The current Docker command passes `USER`, `LOGNAME`, and `USERNAME` so that
Ansible can identify the runtime account even though the Runner's host UID is
not defined in the container image.

## Finish on the Latest Main Branch

After the containerized pipeline succeeds and GitLab shows the merge request
as **Merged**, synchronize the local clone:

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

- The container makes the Ansible runtime reproducible and reviewable.
- Repository code and runtime dependencies have separate lifecycles.
- Non-root execution, an environment allowlist, and `.dockerignore` reduce exposure.
- Containerization does not remove the need for protected Runners, Vault, TLS, tests, or audit logs.

Lab 10 moves from automation runtime engineering to continuous device
visibility through model-driven telemetry.

## References

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
- [Ansible execution environments](https://docs.ansible.com/automation-controller/latest/html/userguide/execution_environments.html)
