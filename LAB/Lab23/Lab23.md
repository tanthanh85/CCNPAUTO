# Optional Lab 23: Explore the Meraki Dashboard API

## Lab Introduction

Meraki provides a cloud-managed hierarchy of organizations, networks, and devices. This lab uses the **Cisco Meraki DevNet Sandbox** and Dashboard API v1 to navigate that hierarchy, follow pagination links, and build a read-only device report.

The sandbox is shared. Do not claim devices, change SSIDs, modify appliance settings, or delete objects.

## Learning Objectives

- Explain organization, network, and device scopes.
- Authenticate with a Meraki API bearer token.
- Navigate from organizations to networks and devices.
- Recognize RFC 5988-style pagination links returned in HTTP headers.
- Interpret HTTP 429 and `Retry-After` without creating unnecessary load.
- Preserve results and logs without exposing the API key.

## Task 1: Obtain Sandbox Access

Open the Meraki sandbox instructions and obtain the current API key or token provided for the lab. If the sandbox requires you to generate a key through the Dashboard profile, follow its current instructions. Treat the value as a password and revoke personal keys after training.

## Task 2: Prepare the Project

Create a private GitLab.com project named `optional_lab23_meraki_api`. Copy the supplied files with VS Code, create `.env` from `.env.example`, and install `requirements.txt` in `.venv`.

Leave `MERAKI_ORG_ID` empty initially. The script selects the first accessible organization; after discovering the desired organization ID, set it explicitly to make later runs deterministic.

## Task 3: Use Postman to Navigate the Hierarchy

Create a private Postman environment containing `base_url` and `api_key`. Add this header without displaying its value:

```text
Authorization: Bearer {{api_key}}
```

Send GET requests in this order:

```text
/organizations
/organizations/{organizationId}/networks
/organizations/{organizationId}/devices
```

Record IDs rather than assuming names are unique. Inspect the response headers for `Link`; when a `rel="next"` URL is present, another page exists.

## Task 4: Run the Python Client

Open `meraki_inventory.py` and locate the loop that follows `response.links["next"]`. Then run:

```bash
python -m py_compile meraki_inventory.py
python meraki_inventory.py
```

The program prints devices and saves organizations, networks, and devices in one timestamped artifact. The debug log records URLs and counts but never the bearer token.

## Task 5: Interpret Meraki Scope

For three devices, relate `networkId` to the network list and identify the model family from `model`. Explain why a serial number is a stronger hardware identifier than a display name. Then identify which operations are organization-scoped and which are network-scoped.

## Task 6: Observe API Safety Signals

Do not deliberately overload the shared sandbox. If Meraki returns HTTP 429 during ordinary use, inspect `Retry-After`, pause for the requested interval, and retry conservatively. Lab 20 provides a local environment for generating repeated 429 responses safely.

## References

- [Meraki Dashboard API v1 introduction](https://developer.cisco.com/meraki/api-v1/)
- [Meraki API authorization](https://developer.cisco.com/meraki/api-v1/authorization/)
- [Meraki API getting started](https://developer.cisco.com/meraki/api-v1/getting-started/)
- [Meraki path schema](https://developer.cisco.com/meraki/api-v1/schema/)

## Key Takeaways

- Meraki resources follow an organization, network, and device hierarchy.
- API keys must be protected and sent through the authorization header.
- IDs are safer automation identifiers than mutable display names.
- Pagination and rate-limit headers are part of the API contract.
