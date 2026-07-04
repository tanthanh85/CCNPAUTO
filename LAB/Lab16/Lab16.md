# Lab 16: Meraki Dashboard API

## Lab Introduction

The Meraki Dashboard API manages organizations, networks, devices, clients, and configuration through a cloud API. This read-only lab uses the official Python SDK to list organizations, retrieve every network through pagination, and display organization-wide device status while respecting shared rate limits.

## Task 1: Prepare Access

Use an instructor-approved Meraki organization or DevNet environment. Enable Dashboard API access and obtain an API key. Create `lab16-meraki-api`, install requirements, and store the key only in `.env`.

## Task 2: List Organizations

```bash
python meraki_lab.py
```

Select the intended organization explicitly with `MERAKI_ORG_ID` rather than relying on the first returned organization when several are available.

## Task 3: Retrieve Networks with Pagination

The SDK uses `total_pages="all"`, following RFC 5988 Link headers until all pages are retrieved. Compare this with manually using `perPage` and `startingAfter`. Pagination is server-side and reduces individual response size.

## Task 4: Interpret Device Status

Correlate device status with network IDs. Count online, offline, alerting, and dormant states. A status response is operational observation, not configuration intent.

## Task 5: Observe Rate-Limit Controls

The SDK is configured with `wait_on_rate_limit=True` and bounded retries. Meraki organization budgets are shared among all applications. Do not deliberately exhaust a production or shared sandbox budget. Inspect API analytics where available.

## Task 6: Extend the Report

Add one efficient organization-wide call, such as device inventory or uplink addresses. Avoid per-device loops when an organization-wide endpoint exists. Export sanitized results to CSV without API keys or sensitive client data.

## Key Takeaways

- Meraki API keys grant organization-scoped authority and require protection.
- RFC 5988 Link headers drive pagination.
- Organization-wide endpoints reduce API calls.
- HTTP 429 and `Retry-After` coordinate fair use of shared budgets.

## References

- [Meraki getting started](https://developer.cisco.com/meraki/api-v1/getting-started/)
- [Meraki pagination](https://developer.cisco.com/meraki/api-v1/pagination/)
- [Meraki rate limits](https://developer.cisco.com/meraki/api-v1/rate-limit/)
