# Optional Lab 25: Explore Cisco ACI with the APIC REST API

## Lab Introduction

Cisco ACI represents data-center policy as managed objects controlled by APIC. This lab uses either the **ACI Simulator 6.0 reservable sandbox** or the **ACI Simulator Always-On sandbox** to authenticate, query object classes, and relate tenants, VRFs, and bridge domains.

The exercise is read-only on both environments. Do not create or delete tenants in the Always-On system. A reservable simulator may permit changes, but configuration work is outside this introductory API lab.

## Learning Objectives

- Explain the APIC managed-object model, classes, attributes, and distinguished names.
- Authenticate through `aaaLogin` and reuse the APIC session cookie.
- Query ACI classes through `/api/node/class`.
- Relate `fvTenant`, `fvCtx`, and `fvBD` objects.
- Interpret `imdata`, object wrappers, attributes, and `totalCount`.
- Preserve a read-only fabric inventory.

## Task 1: Select the Sandbox

Use ACI Simulator 6.0 when a dedicated reservable instance is available. Otherwise, use ACI Simulator Always-On. Obtain the APIC address and credentials from the selected sandbox instructions. Confirm the APIC GUI is reachable and note whether the environment is dedicated or shared.

## Task 2: Prepare the Project

Create `optional_lab25_aci_api` as a private GitLab.com project. Copy the supplied files, create `.env` from `.env.example`, and install requirements in `.venv`.

## Task 3: Authenticate in Postman

Send:

```text
POST {{base_url}}/api/aaaLogin.json
Content-Type: application/json
```

with this payload, using private environment variables:

```json
{
  "aaaUser": {
    "attributes": {
      "name": "{{username}}",
      "pwd": "{{password}}"
    }
  }
}
```

Confirm that the response contains an `aaaLogin` object in `imdata` and that Postman stores the APIC session cookie. Reuse that cookie for subsequent requests.

## Task 4: Query Managed-Object Classes

Send these read-only requests:

```text
GET /api/node/class/topSystem.json
GET /api/node/class/fvTenant.json
GET /api/node/class/fvCtx.json
GET /api/node/class/fvBD.json
```

Each object is wrapped by its class name. Its properties are under `attributes`. Locate `dn`, `name`, and `status` where present. Use the distinguished name to determine the object’s position in the policy tree.

## Task 5: Run the Python Client

Review `aci_inventory.py`, then run:

```bash
python -m py_compile aci_inventory.py
python aci_inventory.py
```

The program queries controller, tenant, VRF, and bridge-domain classes. It prints a tenant table and writes the full object inventory to a timestamped artifact.

## Task 6: Interpret Relationships

Select one tenant and identify the tenant name embedded in its distinguished name. Find VRFs and bridge domains that belong to the same tenant. Explain why an ACI distinguished name carries hierarchy while an object ID in many other controller APIs is opaque.

## Task 7: Close the Session

When practical, send a logout request or close the client session. Review logs for secrets, confirm `.env` is ignored, and commit only source and documentation.

## References

- [Cisco ACI programmability and REST API guide](https://developer.cisco.com/docs/aci/)
- [ACI programmability getting started](https://developer.cisco.com/docs/aci/getting-started/)
- [APIC REST API configuration procedures](https://developer.cisco.com/docs/apic-rest-api-configuration-guide/)

## Key Takeaways

- APIC exposes ACI policy and operational state as managed objects.
- Class queries return `imdata` containing class wrappers and attributes.
- Distinguished names describe object hierarchy and relationships.
- Shared ACI simulators should be explored through read-only operations.
