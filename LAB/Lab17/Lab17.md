# Lab 17: Cisco UCS Manager Automation

## Lab Introduction

Cisco UCS Manager exposes a hierarchical Management Information Tree through its XML API. The Python `ucsmsdk` represents managed objects and external methods as Python classes. This lab inventories blades, rack servers, and service-profile templates. In a reserved UCS Platform Emulator only, learners instantiate one service profile from an approved template.

## Prerequisites and Safety

Reserve the UCS Manager Emulator and UCS Director sandbox or use an instructor-controlled emulator. Do not perform the creation task against production UCS. The `ALLOW_UCS_CHANGES` flag defaults to false.

## Task 1: Prepare the Project

Create `lab17-ucs-manager-api`, copy the files, install `ucsmsdk`, and protect `.env`. Enter the reserved UCS Manager endpoint and credentials.

## Task 2: Understand the UCS MIT

UCS resources are managed objects arranged by distinguished name. `query_classid` retrieves all objects of a class, while `query_dn` retrieves one known path. Commit operations apply staged managed-object changes; external methods such as service-profile instantiation return generated objects.

## Task 3: Inventory Compute Resources

Leave changes disabled and run:

```bash
python ucs_lab.py
```

Interpret chassis/blade or rack-unit DN, serial, model, operational state, and assigned service profile. The script also lists initial and updating service-profile templates.

## Task 4: Select an Approved Template

In UCS Manager, inspect the template's policies, pools, vNICs, boot order, and organization. Set its exact DN in `.env`. The lab profile name uses an `AU` label to represent an Australian server naming requirement; naming alone does not select a physical location or guarantee policy compliance.

## Task 5: Instantiate a Service Profile

Confirm the sandbox is reserved, verify the target name does not exist, and enable:

```dotenv
ALLOW_UCS_CHANGES=true
UCSM_TEMPLATE_DN=org-root/ls-APPROVED_TEMPLATE
UCSM_TARGET_ORG=org-root
UCSM_PROFILE_NAME=LAB17-AU-SERVER-01
```

Run the script again. `ls_instantiate_template` creates the profile hierarchy from the template. Verify the returned DN and inspect the profile in UCS Manager. Do not associate it with hardware unless the exercise explicitly authorizes that operation.

## Task 6: Verify and Clean Up

Use `query_dn` or the UCS Manager UI to confirm the profile type and policy references. Delete only the lab-created profile through the UI or an instructor-approved SDK cleanup, then return the change flag to false.

## Key Takeaways

- UCS Manager exposes a complete hierarchical object model through XML APIs.
- SDK class IDs and distinguished names provide two query strategies.
- Service-profile templates encode reusable server policy.
- Instantiation is a state-changing infrastructure operation and requires reserved scope, validation, and cleanup.

## References

- [UCS Manager developer toolkit](https://developer.cisco.com/docs/ucs-dev-center/ucs-manager/)
- [UCS Python SDK](https://developer.cisco.com/codeexchange/github/repo/CiscoUcs/ucsmsdk/)
- [UCS sandbox](https://developer.cisco.com/docs/ucs-dev-center-ucs-director/sandbox/)
