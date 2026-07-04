# Lab 13: Catalyst Center Intent APIs

## Lab Introduction

Cisco Catalyst Center exposes intent APIs for inventory, assurance, topology, sites, clients, and automation. This read-only lab obtains an authentication token, retrieves network devices, and examines network and client health. The response structure is normalized into tables while raw health objects remain available for interpretation.

## Prerequisites

Reserve or access an instructor-approved Catalyst Center DevNet Sandbox. Use the credentials and URL supplied by the sandbox. API datasets and endpoint versions vary among sandbox releases.

## Task 1: Create and Configure the Project

Create `lab13-catalyst-center-api`, copy the supplied files, install requirements, and create a protected `.env`:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

## Task 2: Understand Token Authentication

The client sends HTTP Basic credentials only to:

```text
POST /dna/system/api/v1/auth/token
```

It then places the returned token in `X-Auth-Token`. Tokens should be cached only for their valid lifetime and must never be logged.

## Task 3: Retrieve Device Inventory

```bash
python catalyst_center_lab.py
```

Interpret hostname, platform, management address, and reachability. Compare the API count with Catalyst Center's Inventory page.

## Task 4: Interpret Health

The script requests network and client health with a current millisecond timestamp. Examine good, fair, bad, idle, wired, and wireless categories present in the response. An empty category can mean no data for the time window rather than perfect health.

Use `jq` or Python to answer:

- How many devices are unreachable?
- Which platform IDs are present?
- Does the response contain wireless health data?
- Which timestamp and time zone apply?

## Task 5: Explore with the API Documentation

Use the Catalyst Center API documentation or built-in developer toolkit to locate site health, device interfaces, and wireless/client endpoints for the active release. Add one read-only call and present it in a table.

## Task 6: Handle Failure Safely

Test an incorrect path and observe 404. Temporarily use an incorrect password and observe authentication failure. Do not retry rejected credentials indefinitely.

## Key Takeaways

- Catalyst Center exchanges Basic credentials for a short-lived API token.
- Intent APIs abstract device-level implementation into controller resources.
- Assurance responses require time-window and dataset interpretation.
- Endpoint availability must be matched to the controller release.

## References

- [Catalyst Center authentication](https://developer.cisco.com/docs/dna-center/2-3-7-7/authentication/)
- [Catalyst Center health monitoring](https://developer.cisco.com/docs/dna-center/2-3-7-4/health-monitoring/)
