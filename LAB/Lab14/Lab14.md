# Lab 14: Cisco Intersight API

## Lab Introduction

Cisco Intersight uses signed API requests rather than transmitting a user password. This lab generates an API key, protects the private key, creates an SDK client, and retrieves physical compute summaries. Learners interpret server name, serial, model, power state, and management mode without changing infrastructure.

## Task 1: Obtain API Access

Use an Intersight account or DevNet sandbox. Generate an API key with read-only privileges where possible. Download the private key once and store it outside the repository:

```bash
chmod 600 /absolute/path/to/SecretKey.txt
```

The key ID is public identification; the private key is a credential and cannot be recovered from Intersight.

## Task 2: Prepare the Project

Create `lab14-intersight-api`, copy the files, install dependencies, and configure `.env` with the key ID and absolute key path. Confirm Git ignores PEM and key files.

## Task 3: Understand HTTP Signatures

For every request, the SDK signs selected headers and the body digest with the private key. Intersight uses the key ID to locate the public key and verify authenticity and integrity. No explicit login session is required.

## Task 4: Retrieve Compute Summaries

```bash
python intersight_lab.py
```

Interpret the table. A physical summary is a consolidated inventory view, not a complete replacement for related processor, memory, storage, alarm, or profile objects.

## Task 5: Explore Filtering and Pagination

Use the Intersight API documentation to add `$filter`, `$select`, `$top`, or `$skip` options supported by the SDK method. Retrieve a bounded page first and record the total count where available.

## Task 6: Protect and Revoke Keys

Confirm the private key never appears in Git, logs, shell history, or artifacts. Revoke the lab key when it is no longer needed. Intersight audit records associate requests with the API key owner and ID.

## Key Takeaways

- Intersight API keys use asymmetric request signing.
- API-key privileges inherit the creating user's RBAC permissions.
- SDK objects reflect the Intersight OpenAPI model.
- Read-only inventory still contains sensitive infrastructure information.

## References

- [Intersight authentication](https://developer.cisco.com/docs/intersight/authentication/)
- [Intersight developer resources](https://developer.cisco.com/docs/intersight/developer-resources-overview/)
