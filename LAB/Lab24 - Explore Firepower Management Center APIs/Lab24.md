# Optional Lab 24: Explore Firepower Management Center APIs

## Lab Introduction

A security operations team manages multiple Firepower Threat Defense devices through Firepower Management Center (FMC). This lab uses the **Firepower Management Center DevNet Sandbox** to authenticate, discover the FMC domain UUID, and retrieve managed-device inventory through read-only APIs.

## Learning Objectives

- Distinguish FMC platform and configuration API paths.
- Generate an access token with basic authentication.
- Capture `X-auth-access-token` and `DOMAIN_UUID` from response headers.
- Retrieve managed-device records safely.
- Interpret FMC object IDs, domains, health, model, and software fields.
- Avoid configuration deployment in a shared lab.

## Task 1: Reserve the FMC Sandbox

Reserve the Firepower Management Center sandbox and follow its VPN instructions. Use only the host and credentials supplied by the active reservation. Open the FMC GUI, then locate **API Explorer** if the sandbox release exposes it. API Explorer is useful for discovering resource structure, parameters, and response schemas, but execute only GET operations in this lab.

## Task 2: Prepare the Project

Create a private project named `optional_lab24_fmc_api`, copy the supplied files, create `.env` from `.env.example`, and install the requirements in `.venv`.

## Task 3: Authenticate with Postman

1. Send `POST {{base_url}}/api/fmc_platform/v1/auth/generatetoken`.
2. Use **Basic Auth** with reservation credentials and send no credential JSON body.
3. Inspect response headers rather than expecting a normal JSON token body.
4. Store `X-auth-access-token` and `DOMAIN_UUID` in private Postman environment variables.
5. Never print or screenshot the access token.

The domain UUID is part of many configuration API paths. It identifies the FMC administrative domain; it is not a device ID.

## Task 4: Retrieve Managed Devices

Send:

```text
GET /api/fmc_config/v1/domain/{domainUUID}/devices/devicerecords?expanded=true
X-auth-access-token: {{access_token}}
Accept: application/json
```

Confirm that the response contains `items`. For one object, identify its object `id`, display `name`, host name, model, health information, and software version where exposed.

## Task 5: Run the Python Client

Review `fmc_inventory.py`, especially response-header processing and domain-specific URL construction. Then run:

```bash
python -m py_compile fmc_inventory.py
python fmc_inventory.py
```

The program writes a timestamped log and raw inventory artifact. It does not create objects, change access-control policies, deploy configuration, or log tokens.

## Task 6: Relate Objects and Deployment

Use API Explorer to locate, but not modify, endpoints for network objects and access policies. Explain why changing an FMC object and deploying policy are separate actions. In production, an automation workflow must validate references, control deployment timing, monitor the deployment task, and preserve audit evidence.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Token header missing | Wrong credentials, incorrect endpoint, or authentication failure |
| HTTP 401 | Expired/invalid access token |
| HTTP 404 | Wrong domain UUID or resource path |
| Empty items | No visible managed devices or sandbox state |

## References

- [Cisco Secure Firewall Management Center API documentation](https://developer.cisco.com/docs/fmc/)
- [Cisco DevNet Sandboxes](https://devnetsandbox.cisco.com/)

## Key Takeaways

- FMC returns authentication state in response headers.
- Domain UUIDs scope configuration resources.
- FMC objects, policies, and deployments have distinct lifecycles.
- Read-only discovery should precede any controlled security-policy change.
