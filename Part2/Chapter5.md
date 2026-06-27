# Chapter 5: Network APIs

## Chapter Purpose

An application programming interface (API) defines how software accesses another system's data and capabilities. Network APIs allow applications to retrieve inventory, observe operational state, provision services, apply configuration, and integrate controllers with business workflows.

This chapter develops API concepts from the request-response exchange through REST, RPC, gRPC, OpenAPI, and HTTP caching. Chapter 6 builds on these foundations with client development, authentication, OAuth, pagination, streaming, and resilient error handling.

## 1. API Fundamentals

An API is a documented contract containing methods, resources, data formats, security requirements, and expected responses. Consumers should not need direct access to the provider's internal database or implementation.

```mermaid
sequenceDiagram
    participant Client as Automation client
    participant API as Controller API
    participant Service as Controller service
    participant Devices as Managed network

    Client->>API: Authenticated request
    API->>Service: Validate and process
    Service->>Devices: Read or change network state
    Devices-->>Service: Result
    Service-->>API: Structured result
    API-->>Client: Status, headers, and representation
```

An API contract normally identifies:

- Methods or operations
- Resource identifiers
- Request and response formats
- Authentication and authorization
- Status and error behavior
- Pagination, filtering, and sorting
- Rate limits
- Versioning and lifecycle policy

### 1.1 API-First Design

API-first development designs and reviews the interface before implementing its internal behavior. Product owners, client developers, security teams, and service developers can validate the contract while changes remain inexpensive.

The provider owns more than endpoint code. It owns documentation, compatibility, monitoring, support, security, and deprecation. Internal services also benefit from these disciplines; an undocumented private interface creates coupling just as easily as an undocumented public one.

## 2. APIs in Network Architecture

Software-defined networking commonly distinguishes northbound and southbound interfaces.

```mermaid
flowchart TB
    Apps["Automation, assurance, and business applications"]
    Apps <-->|northbound APIs| Controller["Network controller"]
    Controller <-->|southbound APIs and protocols| Network["Routers, switches, access points, and fabrics"]
```

Northbound APIs expose topology, inventory, assurance, policy, and provisioning to applications. Southbound APIs and protocols allow a controller to observe and modify network behavior.

A site-provisioning workflow can call a controller's northbound API to create a site, assign address pools, register devices, configure wireless networks, and retrieve health. The controller translates those requests into platform-specific southbound actions.

### 2.1 API Visibility

| Visibility | Consumers | Typical controls |
|---|---|---|
| Internal | Teams inside one organization | enterprise identity, private routing, internal governance |
| Partner | Approved business partners | onboarding, contracts, scoped credentials, quotas |
| Public | External developers | registration, documentation, strong isolation, rate limits |

An internal API should still authenticate callers and apply least privilege. Network location alone is not a sufficient trust decision.

### 2.2 APIs and Web Scraping

When no API exists, software may extract data from rendered web pages. Scraping depends on page structure intended for humans rather than a stable machine contract. Layout changes, JavaScript behavior, access policy, and anti-automation controls can break it.

A supported API is preferable because it provides structured data, documented security, defined limits, compatibility policy, and explicit provider intent. Scraping should be used only when permitted and when its maintenance and legal implications are understood.

## 3. HTTP Resource Methods

REST APIs commonly represent managed entities as resources and use HTTP methods to express intent.

| Method | Typical purpose | Safe | Normally idempotent |
|---|---|---:|---:|
| GET | Retrieve a representation | Yes | Yes |
| POST | Create a subordinate resource or start an action | No | No |
| PUT | Replace a resource at a known URI | No | Yes |
| PATCH | Partially modify a resource | No | Depends on operation |
| DELETE | Remove a resource | No | Yes |

A safe method does not request a state change. An idempotent method has the same intended server state after one or several identical requests.

### 3.1 Idempotency and Network Changes

`GET /devices/123/interfaces` can be repeated without modifying the device. `PUT /devices/123/banner` can replace the complete banner with the same value repeatedly. A `POST /changes` request may create a new job every time it is received.

Retries are therefore not equally safe. A client that loses the response to a POST cannot know whether the server created the job. An idempotency key allows the server to recognize repeated submissions:

```http
POST /v1/change-jobs HTTP/1.1
Host: automation.example.net
Authorization: Bearer <token>
Idempotency-Key: 7b51a176-01af-45c2-822c-2df9207b127a
Content-Type: application/json
```

The provider stores the key with the first result and returns the same logical result when the request is repeated.

### 3.2 Resource-Oriented URIs

Resource paths should normally use nouns:

```text
GET    /v1/devices
GET    /v1/devices/123
POST   /v1/change-jobs
GET    /v1/change-jobs/789
DELETE /v1/webhooks/456
```

Filtering, sorting, field selection, and pagination belong in query parameters when they do not identify a different resource:

```text
GET /v1/devices?site=sg01&status=unreachable&limit=100
```

## 4. Request and Response Structure

An HTTP request contains a method, target URI, headers, and sometimes a body. A response contains a status code, headers, and sometimes a body.

```http
GET /v1/devices/123 HTTP/1.1
Host: controller.example.net
Accept: application/json
Authorization: Bearer <token>
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: private, max-age=30
ETag: "device-123-v42"

{
  "id": "123",
  "hostname": "branch-123-r1",
  "managementIp": "192.0.2.10",
  "status": "reachable"
}
```

### 4.1 Important Headers

- `Accept` states which response formats the client can process.
- `Content-Type` identifies the request or response body format.
- `Authorization` carries credentials or tokens.
- `User-Agent` identifies the client implementation.
- `Location` identifies a created resource or redirect target.
- `Retry-After` tells a client when a retry may be appropriate.
- `Cache-Control`, `ETag`, and `Last-Modified` govern caching and validation.
- `X-Request-ID` or a standard trace header supports correlation.

Clients should validate `Content-Type` before assuming a response contains JSON. Gateways sometimes return an HTML error page even when the normal API is JSON.

### 4.2 JSON and XML

JSON represents objects, arrays, strings, numbers, Booleans, and null values. Its close mapping to common programming structures makes it the dominant format for REST APIs.

```json
{
  "siteId": "sg01",
  "devices": [
    {"id": "123", "role": "edge"},
    {"id": "124", "role": "distribution"}
  ],
  "maintenance": false
}
```

XML provides namespaces, attributes, schemas, and document-oriented capabilities. It remains important for SOAP and network technologies such as NETCONF. The correct format depends on the interface contract rather than personal preference.

## 5. Calling a REST API with Python

The `requests` library provides a direct mapping to HTTP concepts:

```python
import requests

BASE_URL = "https://controller.example.net/api/v1"

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "Authorization": "Bearer <token>",
    "User-Agent": "network-compliance/2.0",
})

response = session.get(
    f"{BASE_URL}/devices",
    params={"site": "sg01", "limit": 100},
    timeout=(3.05, 20),
)

response.raise_for_status()
devices = response.json()

for device in devices["items"]:
    print(device["hostname"], device["status"])
```

The timeout tuple sets separate connection and read limits. Production clients should never depend on an unlimited default wait. Chapter 6 adds classification, retries, rate-limit handling, and terminal-error flow control.

Configuration should supply the base URL and credentials. Tokens should come from an approved secret store or environment integration rather than source code.

## 6. API Architectural Styles

### 6.1 REST

REST is an architectural style centered on resources, representations, a uniform interface, stateless requests, cacheability, and layered systems. HTTP supplies methods, status codes, content negotiation, and caching behavior.

REST works well for web-accessible resources and broad client compatibility. It can be inefficient when clients need many related resources and must make several round trips.

### 6.2 RPC and JSON-RPC

Remote procedure call APIs expose actions rather than only resources. The client invokes a named remote method with parameters.

```json
{
  "jsonrpc": "2.0",
  "method": "cli",
  "params": {"cmd": "show version", "version": 1},
  "id": 1
}
```

Cisco NX-API can accept CLI operations through JSON-RPC. The request identifier connects a response with its request. RPC is natural when the domain consists of explicit operations, but action-oriented contracts can become inconsistent if naming and errors are not standardized.

### 6.3 gRPC

gRPC uses HTTP/2 and Protocol Buffers. A `.proto` interface definition describes services and strongly typed messages, from which tools generate client and server code.

```protobuf
syntax = "proto3";

message InterfaceCounter {
  string device_id = 1;
  string interface_name = 2;
  uint64 input_bytes = 3;
  uint64 output_bytes = 4;
}
```

Binary encoding, multiplexing, streaming, and generated clients make gRPC efficient for service-to-service communication and telemetry. Browser accessibility and human inspection are less direct than with JSON REST APIs.

### 6.4 GraphQL

GraphQL lets clients specify the fields and relationships they need. A dashboard can retrieve device identity, health, and selected interface counters in one query instead of calling several endpoints.

This reduces over-fetching and under-fetching but moves query complexity to the provider. Depth limits, query-cost controls, authorization, and caching require deliberate design.

### 6.5 SOAP

SOAP is an XML-based messaging protocol with mature standards for security, reliability, and transactions. It remains appropriate in enterprise environments that require formal contracts and WS-* capabilities, although it is generally more verbose than REST or gRPC.

### 6.6 Style Selection

| Style | Strong fit | Main trade-off |
|---|---|---|
| REST | Resource APIs and broad HTTP compatibility | Multiple calls for complex related data |
| JSON-RPC | Explicit remote actions | Weaker resource semantics |
| gRPC | Efficient internal services and streaming | Binary tooling and browser limitations |
| GraphQL | Client-selected related data | Query governance and caching complexity |
| SOAP | Formal enterprise security and transactions | XML verbosity and heavier tooling |

## 7. Network API Styles

Network automation commonly uses HTTP-based REST APIs for controllers and services and model-driven protocols such as NETCONF for device configuration and operational state.

### 7.1 REST Constraints

A RESTful design follows these architectural constraints:

- **Client-server:** User interaction is separated from resource management.
- **Stateless:** Every request contains the information needed for processing.
- **Cacheable:** Responses identify whether and how they may be reused.
- **Uniform interface:** Resources, representations, and messages follow consistent semantics.
- **Layered system:** Clients need not know whether gateways, proxies, or other intermediaries exist.
- **Code on demand:** A server may optionally transfer executable behavior to a client.

Statelessness does not prohibit persistent TCP connections. HTTP keepalive can reuse a connection while each request remains independently understandable.

The uniform interface identifies resources with URIs, changes resources through representations, uses self-descriptive messages, and can provide links to related state. A device response may link to its interfaces, site, software image, and active jobs so the client does not construct every URI from undocumented knowledge.

### 7.2 NETCONF and YANG

NETCONF is an IETF protocol for retrieving operational data and managing device configuration. It uses RPC messages, commonly over SSH, and normally encodes YANG-modeled data as XML.

YANG defines the structure, types, constraints, configuration state, operational state, actions, and notifications exposed by a network system. Open models promote cross-vendor consistency, while native models expose vendor-specific capabilities.

```mermaid
flowchart LR
    Client["Python or automation platform"] -->|NETCONF RPC over SSH| Device["Network device"]
    Model["YANG model"] --> Client
    Model --> Device
    Device --> Running[("running datastore")]
    Device --> Candidate[("candidate datastore")]
    Device --> Startup[("startup datastore")]
```

Common NETCONF operations include:

- `get` retrieves configuration and operational data.
- `get-config` retrieves configuration from a selected datastore.
- `edit-config` modifies a target datastore.
- `copy-config` copies one configuration datastore to another.
- `lock` and `unlock` protect a datastore during controlled change.
- `commit` activates candidate configuration where supported.
- `discard-changes` abandons uncommitted candidate changes.

The candidate datastore allows a client to stage a complete change before committing it to running configuration. Validation and confirmed-commit capabilities can reduce the risk of a change that removes management connectivity.

### 7.3 REST and NETCONF

| Characteristic | REST API | NETCONF |
|---|---|---|
| Primary transport | HTTP/HTTPS | SSH, with other secure transports possible |
| Interaction | HTTP request and response | RPC and RPC reply |
| Common encoding | JSON or XML | XML in common implementations |
| State model | Application-defined resources | YANG-modeled configuration and operational state |
| Session behavior | Requests are stateless | Protocol session is stateful |
| Transactions | Provider-specific | Datastores, locking, validation, and commit capabilities |

Controller REST APIs are convenient for site, policy, assurance, and workflow resources. NETCONF is strong when an application needs model-driven device configuration with explicit datastore semantics. A system may use both: REST for controller-level orchestration and NETCONF for direct device operations.

## 8. OpenAPI and API Contracts

The OpenAPI Specification is a language-neutral description format for HTTP APIs. It can define paths, methods, parameters, schemas, responses, and security schemes in YAML or JSON.

```yaml
paths:
  /v1/devices/{deviceId}:
    get:
      parameters:
        - in: path
          name: deviceId
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Device found
        "404":
          description: Device not found
```

An OpenAPI contract supports design review, documentation, mock servers, schema validation, generated client libraries, and contract testing. Swagger tools can edit, visualize, and generate code from the specification.

The contract should be versioned with the service and tested in CI. Generated code is a starting point; security, lifecycle, timeout, and application-specific behavior still require engineering judgment.

## 9. Optimizing API Usage with HTTP Cache Controls

Caching reduces repeated server work, request latency, and bandwidth. It is most useful for representations that are read frequently and change less often than they are requested.

### 9.1 Freshness

The server can permit reuse for a defined period:

```http
Cache-Control: private, max-age=60
```

`private` limits storage to the client cache. `public` allows shared caches. `s-maxage` defines freshness for shared caches. `Expires` provides an absolute timestamp but is less flexible than `Cache-Control`.

Static device platform capabilities may remain fresh for hours, while live interface state may be fresh for only seconds. Sensitive tokens and personalized responses usually require `private` or `no-store`.

### 9.2 Revalidation with ETag

When a client has an older representation and its ETag, it can ask whether the resource changed:

```http
GET /v1/devices/123 HTTP/1.1
If-None-Match: "device-123-v42"
```

If unchanged, the server returns:

```http
HTTP/1.1 304 Not Modified
ETag: "device-123-v42"
```

The client reuses its body, avoiding database serialization and network transfer.

```mermaid
sequenceDiagram
    participant Client
    participant API

    Client->>API: GET /devices/123
    API-->>Client: 200 + body + ETag v42
    Note over Client: Cache body
    Client->>API: GET + If-None-Match v42
    API-->>Client: 304 Not Modified
    Note over Client: Reuse cached body
```

`Last-Modified` and `If-Modified-Since` provide time-based validation but may be less precise than entity tags.

### 9.3 Directive Meaning

| Directive | Meaning |
|---|---|
| `max-age=N` | Response is fresh for N seconds |
| `no-cache` | Storage is allowed, but revalidation is required before reuse |
| `no-store` | Response must not be stored |
| `private` | Only a private client cache may store it |
| `public` | Shared caches may store it |
| `must-revalidate` | Stale content must not be reused without validation |
| `no-transform` | Intermediaries should not alter the representation |
| `only-if-cached` | Client requests a cached response without contacting origin |

`no-cache` does not mean “do not store”; that is the role of `no-store`.

### 9.4 Safe Cache Design

Cache keys must include every request property that changes the representation, such as tenant, authorization scope, language, or selected fields. The `Vary` response header tells caches which request headers affect content.

Do not cache unsafe methods by default. Invalidate or version affected representations after a change. A configuration job response can be cached only briefly while terminal audit records may use conditional retrieval with an ETag.

## 10. API Selection and Consumption Checklist

- Is the interface supported and documented?
- Are methods aligned with resource behavior?
- Is retry safety understood for every operation?
- Are request and response schemas validated?
- Are authentication and authorization appropriate to API visibility?
- Does the chosen style match browser, streaming, transaction, and performance needs?
- Is the OpenAPI or interface definition version controlled?
- Are timeouts explicit?
- Can stable GET responses use freshness or conditional caching?
- Are sensitive and user-specific responses protected from shared caches?

## Chapter Summary

Network APIs expose platform capabilities through documented methods, resources, formats, and security controls. REST uses HTTP resource semantics, while RPC, gRPC, GraphQL, and SOAP address different operational and integration needs.

Safe and idempotent behavior determines whether a request can be retried. OpenAPI makes contracts reviewable and supports documentation, testing, and client generation. HTTP cache controls improve API efficiency through freshness and conditional validation, provided cache scope, identity, staleness, and invalidation are handled correctly.
