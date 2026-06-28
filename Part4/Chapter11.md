# Chapter 11: NETCONF and RESTCONF

## Chapter Purpose

NETCONF and RESTCONF replace fragile screen scraping with structured, model-driven network management. Both use YANG models to describe valid data, but they differ in transport and operations. This chapter develops the protocols through Cisco IOS XE configuration scenarios.

## 1. Why Model-Driven Management?

CLI syntax varies across platforms and releases. A model describes data independently of screen layout, including hierarchy, type, constraints, configuration, and operational state.

```mermaid
flowchart LR
    Intent["Automation intent"] --> Model["YANG data model"]
    Model --> Protocol["NETCONF or RESTCONF"]
    Protocol --> IOSXE["Cisco IOS XE datastore"]
    IOSXE --> State["Configuration and operational state"]
```

Model-driven management enables schema validation before a device accepts a change and makes data easier for software to process.

## 2. YANG Fundamentals

YANG is a data modeling language maintained through the IETF NETMOD work. A **module** has a namespace and prefix. Common nodes include:

- `container`: groups related nodes.
- `list`: repeatable entries identified by one or more keys.
- `leaf`: one typed value.
- `leaf-list`: repeated scalar values.
- `choice` and `case`: mutually exclusive structures.
- `rpc` and `action`: operations defined by a model.
- `notification`: asynchronous event data.

Cisco IOS XE exposes native Cisco models and standards-based OpenConfig or IETF models where supported. Check the device's YANG library because platform and release determine availability.

## 3. NETCONF Architecture

NETCONF, currently defined by RFC 6241, normally runs over SSH on TCP port 830. Client and server exchange `<hello>` messages to advertise capabilities. The client then sends XML RPC requests and receives `<rpc-reply>` responses.

```mermaid
sequenceDiagram
    participant C as NETCONF client
    participant D as IOS XE device
    C->>D: SSH connection to TCP 830
    C->>D: client hello and capabilities
    D-->>C: server hello and capabilities
    C->>D: rpc get-config / edit-config
    D-->>C: rpc-reply data / ok / rpc-error
    C->>D: close-session
```

NETCONF datastores can include `running`, `candidate`, and `startup`, depending on advertised capabilities. Candidate configuration permits staging and validation before commit. Locking prevents competing clients from changing the same datastore during a transaction.

Key operations include `<get>`, `<get-config>`, `<edit-config>`, `<copy-config>`, `<delete-config>`, `<lock>`, `<unlock>`, `<commit>`, and `<close-session>`.

## 4. Reading and Changing Configuration

On IOS XE, `netconf-yang` enables the service. A filtered read avoids retrieving an entire datastore.

```python
from ncclient import manager

with manager.connect(
    host="10.10.20.48", port=830,
    username="automation", password="secret",
    hostkey_verify=True, device_params={"name": "iosxe"},
) as session:
    reply = session.get_config(
        source="running",
        filter=("subtree", """
          <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface><name>GigabitEthernet2</name></interface>
          </interfaces>"""),
    )
    print(reply.xml)
```

An `<edit-config>` payload must use the correct namespace and hierarchy. The `default-operation` can be `merge`, `replace`, or `none`; node-level operations can create, merge, replace, delete, or remove data. Use precise edits because replacing a parent container may remove sibling configuration.

## 5. NETCONF Error Handling

An `<rpc-error>` can include error type, tag, severity, path, message, and vendor information. Treat schema violations differently from temporary transport failures. Retrying malformed configuration will not help; a timeout may be retried only after determining whether the original operation took effect.

```mermaid
flowchart TD
    Call["Send RPC"] --> Reply{"Reply received?"}
    Reply -->|yes| Err{"rpc-error?"}
    Err -->|no| Verify["Verify intended state"]
    Err -->|yes| Classify["Classify schema, access, lock, or resource error"]
    Reply -->|no| Read["Reconnect and read current state"]
    Read --> Decide["Retry only if safe"]
```

## 6. RESTCONF Architecture

RESTCONF, defined by RFC 8040, maps YANG data to HTTP resources. It commonly uses HTTPS on TCP 443. The API root is typically `/restconf`; data resources appear below `/restconf/data`, while model-defined operations appear below `/restconf/operations`.

Use these media types:

- `application/yang-data+json`
- `application/yang-data+xml`

`Accept` requests a response representation. `Content-Type` describes the request body.

## 7. RESTCONF Operations

```python
import requests

url = "https://10.10.20.48/restconf/data/ietf-interfaces:interfaces"
headers = {"Accept": "application/yang-data+json"}
r = requests.get(url, headers=headers, auth=("automation", "secret"), timeout=15)
r.raise_for_status()
interfaces = r.json()["ietf-interfaces:interfaces"]["interface"]
```

`GET` retrieves data, `POST` creates a child resource, `PUT` creates or replaces a resource at a specific URI, `PATCH` changes selected content, and `DELETE` removes a resource. A RESTCONF URI uses module-qualified names where needed and URL-encoded list keys.

To configure a loopback, send a JSON body whose top-level member matches the target resource. After the write, retrieve the interface and verify both configuration and operational state.

## 8. NETCONF or RESTCONF?

| Consideration | NETCONF | RESTCONF |
|---|---|---|
| Encoding | XML | JSON or XML |
| Transport | SSH, usually 830 | HTTPS, usually 443 |
| Transactions | Rich datastore, lock, and commit capabilities | Familiar HTTP resource operations |
| Best fit | Configuration workflows needing transaction control | Web-style integration and simple resource access |

Both protocols are only as portable as the selected YANG model and device support. Standards-based models improve consistency, while native models often expose deeper platform features.

> **Study guide takeaway:** YANG defines the contract; NETCONF and RESTCONF carry requests against that contract. Reliable automation discovers capabilities, sends minimal validated changes, interprets structured errors, and verifies resulting state.

## Chapter Summary

NETCONF offers XML RPC operations, datastores, locks, and commit behavior over SSH. RESTCONF presents YANG-modeled data as HTTP resources using JSON or XML. Cisco IOS XE supports both, allowing applications to configure interfaces, VLANs, routes, and other modeled functions without parsing CLI output.
