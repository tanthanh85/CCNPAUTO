# Lab 9: Package a Network Application with Docker

## Lab Introduction

Python virtual environments improve dependency isolation, but they still depend on the host operating system and local setup. Docker packages application code, interpreter, libraries, and execution metadata into an immutable image. This lab packages a Netmiko collector that runs `show ip interface brief`, parses the response with TextFSM, and prints a table.

## Learning Objectives

- Build and inspect a Docker image.
- Use layer caching and `.dockerignore`.
- Run as a non-root user.
- Inject configuration at runtime instead of baking credentials into an image.
- Connect a containerized Netmiko client to a reserved IOS XE sandbox.
- Explain image portability and its architectural limits.

## Task 1: Create the Project

Create and clone `lab9-docker-interface-collector`, then copy `app.py`, `requirements.txt`, `Dockerfile`, `.dockerignore`, `.gitignore`, and `.env.example` from the Lab 9 folder.

Test outside Docker first:

```bash
source "$HOME/.venvs/ccnpauto/bin/activate"
python -m pip install -r requirements.txt
DEMO_MODE=true python app.py
```

Demo mode produces deterministic records and is later used by the standalone Kubernetes lab.

## Task 2: Review the Application

`InterfaceCollector` supports two execution paths. Demo mode returns local records. Live mode validates runtime variables, connects with Netmiko, runs `show ip interface brief`, requests TextFSM parsing, and disconnects in `finally`. The program refuses a raw string because a missing template could otherwise produce plausible but incorrect iteration.

## Task 3: Review the Dockerfile

The image uses `python:3.13-slim`, installs fixed dependency ranges, copies only required source, and changes to an unprivileged account. Credentials are deliberately absent. `.dockerignore` prevents `.git` and `.env` from entering the build context.

Build the image:

```bash
docker build --tag lab9-interface-collector:1.0 .
docker image inspect lab9-interface-collector:1.0
docker history lab9-interface-collector:1.0
```

## Task 4: Run the Portable Demo

```bash
docker run --rm \
  --env DEMO_MODE=true \
  lab9-interface-collector:1.0
```

The same command behaves consistently on any compatible Linux container runtime and CPU architecture for which the image is built. Docker portability does not mean every host can reach the same router; VPN routes, DNS, certificates, credentials, and firewall policy remain runtime concerns.

## Task 5: Run Against the Reserved Router

Create `.env` from the example and protect it:

```bash
cp .env.example .env
chmod 600 .env
```

Enter the reserved IOS XE connection values and run:

```bash
docker run --rm --env-file .env lab9-interface-collector:1.0
```

If the container cannot reach a VPN route that exists on the host, test with host networking on Linux:

```bash
docker run --rm --network host --env-file .env \
  lab9-interface-collector:1.0
```

Host networking reduces isolation and must be used deliberately. Never copy `.env` into the image or commit it.

## Task 6: Inspect Reproducibility and Failure

Run with a missing password and observe the controlled error. Then use `docker run --entrypoint sh` to inspect the filesystem and confirm the process account is not root:

```bash
docker run --rm --entrypoint sh lab9-interface-collector:1.0 \
  -c 'id && python --version && pip list'
```

## Task 7: Tag and Clean Up

```bash
docker tag lab9-interface-collector:1.0 lab9-interface-collector:latest
docker image ls lab9-interface-collector
git add .
git commit -m "Package interface collector with Docker"
git push
```

## Key Takeaways

- Images package runtime dependencies and application code into versioned artifacts.
- Runtime settings and secrets remain external to the image.
- Non-root execution and small build contexts reduce risk.
- Containers improve portability but do not erase network or platform dependencies.

Lab 10 runs the same image as a Kubernetes batch workload without requiring a sandbox.
