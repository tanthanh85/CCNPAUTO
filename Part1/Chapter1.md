# Chapter 1: Software Design Foundations

## Chapter Introduction

Network automation starts with code, but useful automation quickly grows beyond a script. The moment several engineers depend on it, the software needs requirements, interfaces, security controls, testing, state management, and a reliable delivery process. This chapter explains those foundations in the language of network operations.

As you work through the chapter, follow one central question: **How does an operator's intent become a safe, observable change in the network?** The answer connects front-end applications, APIs, job queues, workers, databases, controllers, and network devices.

## 1. From Network Management to Software-Driven Operations

Early enterprise networks were managed one device at a time. An administrator connected to a router or switch, entered commands, checked the result, and repeated the process on the next device. That approach was workable for a small environment, but it became slow and risky as networks grew. Two engineers could perform the same task differently, and even a small typing mistake could create an outage.

The adoption of the Simple Network Management Protocol (SNMP) introduced a standard relationship between agents on managed devices and central managers. Network management systems could collect status and performance data across many devices.

Virtualization then separated logical functions from dedicated hardware. Servers, routers, firewalls, and load balancers could be represented and controlled through software. APIs exposed those functions to automation, while software-defined networking separated control decisions from packet forwarding.

Operations consequently progressed through several stages:

```mermaid
flowchart LR
    Monitor["Monitor state"] --> React["React manually"]
    React --> Model["Model and validate"]
    Model --> Automate["Automate individual tasks"]
    Automate --> Orchestrate["Orchestrate complete workflows"]
    Orchestrate --> Optimize["Continuously optimize from telemetry"]
```

The distinction between automation and orchestration is important. Monitoring can report that an interface is down. Automation can gather diagnostics or apply a known correction. Orchestration coordinates the complete operational process: identify the affected service, confirm the approved policy, make the change, validate the result, update the ticket, and notify the right team.

The following view connects that operational evolution to a modern automation platform:

```mermaid
flowchart TB
    Telemetry["Device telemetry and events"] --> Observe["Monitoring and assurance"]
    Observe --> Decision["Policy or operator decision"]
    Decision --> Workflow["Automation workflow"]
    Workflow --> Controller["Controller or device API"]
    Controller --> Network["Routers, switches, firewalls, wireless"]
    Network --> Validation["Post-change validation"]
    Validation --> Observe
```

This is a closed-loop system. The application does not assume that a successful API response means the network is healthy; it observes the result and compares actual state with intended state.

### 1.1 Software Engineering and Development

Software engineering emphasizes problem decomposition, requirements, architecture, trade-offs, and delivery strategy. Software development emphasizes implementation and integration. In practice, these responsibilities overlap. A developer who understands architectural consequences writes safer code, while an architect who understands implementation constraints makes more realistic decisions.

Network automation requires both perspectives. A script may configure one switch successfully, but an engineered application must manage credentials, concurrency, failure, auditability, multiple platforms, and safe recovery across thousands of devices.

### 1.1 From Device Management to Business Services

The progression was not simply a matter of replacing the CLI with Python. Early management systems concentrated on individual components: whether a device was reachable, whether an interface was up, and whether a counter crossed a threshold. Those measurements were useful, but they did not prove that the business service worked. Every router could answer SNMP while users remained unable to work because identity, DNS, firewall policy, or an application dependency had failed.

The FCAPS model organized traditional responsibilities into **fault, configuration, accounting, performance, and security** management. These categories remain relevant, although modern applications combine their data into service workflows. For example, opening a branch is not complete merely because separate router, switch, wireless, firewall, and monitoring tickets have closed. A service workflow coordinates shared data, invokes the appropriate controllers, verifies end-to-end behavior, and records one correlated result.

This shift also changed the NOC. Operators increasingly use APIs, source-of-truth data, event correlation, and automated diagnostics rather than watching isolated alarms. Software skills therefore complement network knowledge; they do not replace the understanding of routing, segmentation, dependencies, and failure domains needed to judge an automated action.

### 1.2 Engineering and Development Responsibilities

Software engineering begins with the problem and its constraints. It identifies stakeholders, quality requirements, risks, system boundaries, and trade-offs before selecting structures and technologies. Software development turns those decisions into code, tests, packages, and observable behavior. The roles overlap in a collaborative team, but the distinction explains why a shared production service requires more than correct syntax.

A one-time inventory script may reasonably remain small. Once it stores credentials, accepts requests, schedules jobs, persists state, and changes devices, decisions about authorization, concurrency, interfaces, deployment, recovery, and support become part of the work. At that point, the script has become a software product.

## 2. Distributed Application Structure

A distributed application contains components that run in separate processes or systems and communicate over a network. Distribution enables independent scaling, geographic placement, and fault isolation, but it introduces latency, partial failure, data-consistency challenges, and operational complexity.

```mermaid
flowchart LR
    User["Network engineer"] -->|HTTPS| DNS["DNS"]
    DNS --> LB["Redundant load balancers"]
    LB --> API1["Automation API 1"]
    LB --> API2["Automation API 2"]
    API1 --> Inventory[("Inventory and job data")]
    API2 --> Inventory
    API1 --> Queue["Job queue"]
    API2 --> Queue
    Queue --> Worker1["Configuration worker"]
    Queue --> Worker2["Validation worker"]
    Worker1 --> Devices["Routers, switches, and controllers"]
    Worker2 --> Devices
    API1 --> Telemetry["Logs, metrics, and traces"]
    Worker1 --> Telemetry
```

An engineer submitting an access-list change for 500 branches interacts with the front end. The request enters through a load balancer and reaches an API instance. The API authenticates the user, validates the change, records a job, and publishes device tasks. Workers execute those tasks at a controlled rate and report progress. Keeping the browser connection open until every device finishes would make the workflow fragile; returning a job identifier separates user interaction from long-running execution.

### 2.1 Front End

The front end may be a browser interface, mobile application, command-line client, or another software system. It presents data, collects input, manages interface state, and calls APIs.

Its responsibilities include:

- Rendering controls and results
- Performing user-friendly input checks
- Managing authentication tokens securely
- Handling latency, timeouts, and failures
- Displaying asynchronous job status
- Producing client-side telemetry

Front-end validation improves usability but does not establish trust. A caller can bypass the interface or modify a request, so the back end must enforce validation, authentication, and authorization.

### 2.2 Back End

The back end applies business rules and controls protected operations. It authenticates callers, validates input, reads and writes data, calls dependent services, publishes events, and returns consistent responses.

Interfaces may use REST, GraphQL, gRPC, WebSocket connections, message queues, or device protocols such as NETCONF and RESTCONF. A contract should define:

- Methods and resource paths
- Request and response schemas
- Authentication and authorization
- Error structure
- Rate limits
- Versioning and compatibility
- Timeout and retry expectations

### 2.3 Stateless and Stateful Components

A stateless service does not rely on local session data between requests. Any healthy instance can process the next request because shared state is stored externally. Stateless API and worker tiers are easier to replace and scale horizontally.

Stateful components retain information across interactions. Databases, queues, topology stores, and caches need replication, backup, consistency, and recovery design. State should be placed deliberately in services built to protect it rather than hidden in an application process.

If a worker records a job only in local memory, its failure loses progress. If job and device state are persisted, another worker can resume safely. Operation identifiers are still needed to prevent a reassigned task from configuring a device twice.

### 2.4 Load Balancing

A load balancer provides a stable service endpoint and distributes requests across healthy instances.

| Algorithm | Behavior | Suitable condition |
|---|---|---|
| Round robin | Sends requests in sequence | Similar stateless instances |
| Weighted round robin | Sends more traffic to stronger instances | Unequal capacity |
| Least connections | Selects the least-busy instance | Long-lived connections |
| Least response time | Uses connection and latency observations | Uneven real-time performance |
| Hash-based | Maps a stable property to an instance | Affinity is required |

Layer 4 load balancing uses addresses and transport ports. Layer 7 load balancing understands HTTP hostnames, paths, headers, methods, and cookies and may terminate TLS.

Health checks determine whether an instance should receive traffic. A TCP connection proves only that a process listens on a port. Readiness should confirm that the application can perform required work. Liveness answers whether the process should be restarted; it should not fail merely because a remote dependency experiences a short outage.

## 3. Architecture as a System Blueprint

Software architecture describes the structures needed to reason about a system: its elements, relationships, interfaces, properties, and governing decisions. It translates business needs into a technical organization.

Architecture documents:

- Component responsibilities
- Interactions and dependencies
- Data ownership and flow
- Trust and failure boundaries
- Technology constraints
- Quality priorities and trade-offs
- Deployment and operational assumptions

It also provides a shared reference for product owners, developers, security teams, network engineers, and operators. A decision record should explain important choices and alternatives, not merely show the final diagram.

### 3.1 Architectural Views and Decisions

No single diagram can answer every architectural question. A context view shows users and external systems; a deployment view shows services, databases, queues, and controllers; a component view explains internal responsibilities; and a sequence view shows behavior over time. Security and data views add trust boundaries, ownership, classification, and lifecycle. Together, these perspectives serve developers, operators, security reviewers, and business stakeholders without forcing one overloaded picture to do every job.

Architecture also records reasoning. A queue protects an API from slow device operations, but introduces duplicate delivery and backlog management. Microservices support independent deployment, yet add network calls, versioned contracts, and operational overhead. Important choices should be captured in short architecture decision records containing context, options, the selected decision, and consequences. Later teams can then revise a decision with an understanding of the assumptions behind it.

## 4. Requirements and Constraints

Architecture begins with agreed requirements.

### 4.1 Functional Requirements

Functional requirements describe what the application must do. A network compliance platform may need to:

- Discover managed devices.
- collect configuration and operational state.
- compare state with approved policy.
- produce a compliance report.
- create a controlled remediation job.
- record approval and execution history.

A user story states a goal from a user perspective: “As a network operator, I want to see devices that violate the approved NTP policy so that I can remediate them.” A use case adds interaction and system detail, including input, normal path, alternate path, output, and permissions.

Functional requirements should be concise, testable, unambiguous, and specific about actors, data, failure behavior, and prohibited actions.

### 4.2 Nonfunctional Requirements

Nonfunctional requirements describe how well the system performs its functions. They include performance, availability, resilience, scalability, security, usability, interoperability, testability, portability, and maintainability.

“The inventory API must be fast” cannot be tested consistently. “The inventory API shall return 95 percent of queries for 10,000 devices within 500 ms under normal production load” can guide design and acceptance testing.

Quality attributes interact. Strong consistency can increase latency; more telemetry can increase cost; distribution can improve scale while adding failure modes. Chapter 2 develops this trade-off analysis.

### 4.3 Constraints

Constraints are decisions or limits the team cannot freely change, such as:

- Required programming languages or runtime
- Existing identity and database platforms
- Mandatory cloud region or on-premises deployment
- Regulatory and data-residency obligations
- Approved device protocols
- Legacy interfaces
- Budget and delivery dates

Constraints should be documented separately from functional needs so future teams understand which choices were intentional and which were imposed.

## 5. Architectural Models

### 5.1 Monolithic Architecture

A monolith packages the application's major functions as one deployable unit. A well-designed monolith can still contain clear internal modules.

It offers simple deployment, local calls, straightforward transactions, and easier debugging for small systems. The whole application must usually be scaled and released together, and weak internal boundaries can turn a growing codebase into tightly coupled code.

A modular monolith is often a sensible beginning for an internal automation platform. Inventory, rendering, scheduling, execution, and auditing remain separate modules without introducing network calls between them.

### 5.2 Service-Oriented Architecture

Service-oriented architecture organizes reusable business functions as services with explicit contracts. Services can use different technologies and may communicate through shared integration middleware.

SOA supports enterprise interoperability and reuse, but centralized transformation and routing can become a bottleneck or governance burden if too much behavior accumulates in the integration layer.

### 5.3 Microservices Architecture

Microservices divide the application into independently owned and deployed services aligned with business capabilities.

```mermaid
flowchart LR
    Gateway["API gateway"] --> Inventory["Inventory service"]
    Gateway --> Change["Change service"]
    Change --> Events["Event bus"]
    Events --> Execute["Execution service"]
    Events --> Audit["Audit service"]
    Inventory --> IDB[("Inventory data")]
    Change --> CDB[("Change data")]
```

Independent deployment and scaling are valuable when components have different workloads or owners. Costs include network latency, partial failure, distributed data consistency, API compatibility, security surfaces, and observability requirements.

Services should own their data rather than share tables as an undocumented interface. A workflow spanning services may use eventual consistency and compensating actions instead of one global transaction.

### 5.4 Event-Driven Architecture

Event-driven systems publish state changes that consumers process asynchronously. A producer does not need to know every consumer.

Publish/subscribe delivers an event to interested consumers. Competing consumers share work from a queue. Event streaming retains an ordered history that consumers can read and replay.

This model buffers load and allows new consumers to be added without modifying producers. It also introduces duplicate delivery, ordering, schema evolution, replay, and troubleshooting challenges. Consumers should be idempotent, and repeatedly failing messages need controlled isolation and recovery.

### 5.5 Selecting and Combining Models

| Model | Strong fit | Primary cost |
|---|---|---|
| Modular monolith | Small teams and cohesive systems | Limited independent deployment |
| SOA | Enterprise reuse and integration | Middleware and governance complexity |
| Microservices | Independent ownership and scaling | Distributed-system operations |
| Event-driven | Asynchronous workflows and high event volume | Eventual consistency and diagnosis |

Architectures are commonly combined. A modular monolith can publish events. A microservices platform may use synchronous APIs for queries and events for state changes. The smallest architecture that satisfies the requirements is usually the easiest to deliver and operate.

## 6. Software Development Lifecycle

The software development lifecycle organizes delivery from problem definition to operation.

```mermaid
flowchart LR
    Plan["Plan"] --> Define["Define requirements"]
    Define --> Design["Design"]
    Design --> Build["Build"]
    Build --> Test["Test"]
    Test --> Deploy["Deploy"]
    Deploy --> Operate["Operate and improve"]
    Operate --> Plan
```

### 6.1 Planning and Definition

Planning establishes the business problem, stakeholders, risks, scope, and intended outcome. Definition turns that context into functional requirements, measurable quality attributes, constraints, and acceptance criteria.

### 6.2 Design and Build

Design identifies components, interfaces, data flow, deployment, security boundaries, and trade-offs. Building implements the design with source control, coding standards, automated tests, and dependency management.

### 6.3 Test, Deploy, and Operate

Testing verifies units, integrations, complete workflows, performance, security, and acceptance criteria. Deployment may use a pilot, canary, rolling, or blue-green approach. Operation includes monitoring, incident response, maintenance, feedback, and improvement.

### 6.4 Deliverables and Feedback

Each lifecycle phase should produce evidence for the next one. Planning defines the problem, scope, stakeholders, and success criteria. Requirements produce testable behavior and quality scenarios. Design produces architecture views, contracts, security controls, and decision records. Implementation produces code, tests, dependency declarations, and build instructions. Testing identifies which requirements were evaluated against which artifact, while deployment records configuration, approvals, migration, and verification.

Operations completes the loop by returning incidents, performance measurements, and user experience to planning. This matters in network automation because a workflow that succeeds in a laboratory may still be too slow across distant sites or difficult to recover during controller failure. Operational evidence should therefore influence the next iteration rather than remain in a separate support system.

## 7. Development Models

### 7.1 Waterfall

Waterfall moves through phases sequentially. Each phase is completed and approved before the next begins. It provides clear documentation and formal control when requirements are stable, but late discoveries are expensive because earlier work may need to be repeated.

### 7.2 Agile

Agile delivers small increments through short feedback cycles. It emphasizes working software, stakeholder collaboration, responsiveness to change, technical excellence, and regular process improvement.

Agile does not mean absence of architecture or documentation. Teams still need system-wide direction, measurable outcomes, and controlled interfaces. Iteration changes the timing and scope of planning rather than eliminating it.

### 7.3 Scrum, Kanban, Extreme Programming, and Lean

- **Scrum** organizes work into time-boxed sprints with defined goals and review points.
- **Kanban** visualizes flow and limits work in progress.
- **Extreme Programming** emphasizes short feedback cycles, close stakeholder participation, and disciplined engineering practices.
- **Lean** prioritizes value, eliminates waste, defers irreversible decisions until sufficient information exists, and builds quality into the process.

A network automation team may use Kanban for unpredictable operational requests while using sprint planning for larger platform capabilities. The method should serve the work rather than become an administrative objective.

### 7.4 Selecting a Development Model

No development model is universally superior. The choice depends on requirement stability, delivery frequency, regulatory expectations, technical uncertainty, team structure, and the cost of changing direction. Waterfall can remain appropriate when a product has fixed contractual milestones, formal sign-off, and expensive deployment constraints. Agile methods are usually stronger when users can provide frequent feedback and the team can release useful increments without waiting for the complete product.

In practice, many organizations use a hybrid approach. A data-center migration may have fixed architecture gates, procurement dates, and change windows that resemble waterfall planning. Within that program, the automation team may still deliver inventory discovery, validation, provisioning, and reporting capabilities in short Agile increments. The outer program supplies governance, while the inner development cycle reduces technical uncertainty through frequent working software.

Consider a team building branch-deployment automation. During the first sprint, it may create a read-only workflow that validates inventory and address data. The next sprint adds controller provisioning in a lab, followed by approval and rollback functions. Stakeholders can inspect each increment and correct assumptions early. By contrast, waiting six months to demonstrate the entire workflow could reveal too late that the source-of-truth data is incomplete or that the controller's task model differs from the original design.

Scrum is useful when a stable product team can commit to a sprint goal. Kanban fits support and platform teams whose incoming work is less predictable. Extreme Programming practices such as test-driven development, pair programming, continuous integration, and small releases can strengthen either model. Lean principles help the team question whether a feature creates customer value or merely adds handoffs, inventory, and delay.

Regardless of the model, teams should avoid confusing activity with progress. Completing many tickets does not prove that the application is safer or more useful. Working software, measurable service outcomes, defect trends, user feedback, and operational stability provide stronger evidence.

## 8. DevOps and Delivery Automation

DevOps connects development and operations through shared responsibility, automation, and rapid feedback.

Continuous integration merges changes frequently and validates them with automated builds and tests. Continuous delivery keeps approved software releasable. Continuous deployment automatically releases changes that pass all required controls.

Useful delivery and operational metrics include:

- Deployment frequency
- Lead time for change
- Change failure rate
- Mean time to recovery
- Release volume
- Service-request and incident trends

Automation reduces human error and creates repeatable procedures, but unsafe logic becomes repeatably unsafe. Reviews, tests, policy checks, limited permissions, staged rollout, and observability remain necessary.

### 8.1 DevOps as an Operating Model

DevOps is often mistaken for a job title or a collection of pipeline products. More accurately, it is an operating model in which the people who design and build a service share responsibility for deploying, observing, supporting, and improving it. Operations knowledge influences design before release, while production evidence returns directly to development.

This shared responsibility shortens a familiar and costly feedback loop. In a traditional handoff, developers may deliver a package that works in their environment, while operators discover missing configuration, unclear health checks, or unsafe recovery behavior during installation. A DevOps team addresses those questions while the feature is being designed. Deployment manifests, dashboards, alerts, runbooks, and rollback procedures become part of the deliverable rather than follow-up work.

For network automation, the collaboration must also include network domain experts and security teams. A developer may understand the controller API but not the operational effect of replacing a route policy on hundreds of WAN edges. Conversely, a network engineer may know the intended routing behavior but not the consequences of an unbounded retry loop. The safest solution emerges when those perspectives shape one workflow.

### 8.2 From Commit to Verified Release

A mature pipeline turns a source change into evidence. It checks formatting and static analysis, runs unit and contract tests, builds an immutable artifact, scans dependencies and the container image, deploys to a representative environment, and performs integration and acceptance tests. If the artifact is approved, the same digest is promoted rather than rebuilt.

```mermaid
flowchart LR
    Commit["Reviewed commit"] --> CI["Build and automated checks"]
    CI --> Artifact["Signed immutable artifact"]
    Artifact --> Stage["Staging deployment"]
    Stage --> Verify["Functional, security, and resilience tests"]
    Verify --> Canary["Limited production canary"]
    Canary --> Observe["Service and change metrics"]
    Observe -->|healthy| Promote["Controlled promotion"]
    Observe -->|unhealthy| Rollback["Stop and recover"]
```

Suppose a new compliance worker supports another IOS XE release. The pipeline can test parsing against recorded sanitized responses, run contract tests against a sandbox, and deploy one worker instance that handles a limited device group. If parse failures or job duration rise, the rollout stops before the entire inventory is affected.

Delivery metrics should be interpreted together. A higher deployment frequency is beneficial only when change failure rate and recovery remain acceptable. Short lead time is not useful if teams bypass review or accumulate operational debt. Likewise, mean time to recovery improves when releases are observable, reversible, and small enough to diagnose—not merely when incidents are closed quickly.

## 9. Reviews and Testing

Architecture review confirms that design decisions satisfy requirements and quality priorities. Code review checks implementation, tests, security, interfaces, naming, documentation, and alignment with architecture.

Review can involve peers, internal stakeholders, or independent assessors. Findings should be documented and treated as shared learning rather than personal criticism.

### 9.1 Testing Levels

- **Unit testing** verifies a function, method, or class in isolation.
- **Integration testing** verifies interactions among components.
- **System testing** evaluates the complete application against requirements.
- **Acceptance testing** confirms suitability for users and stakeholders.

White-box testing uses knowledge of internal implementation. Black-box testing evaluates behavior through public interfaces. Gray-box testing uses partial knowledge.

An automation renderer can be unit-tested with desired-state input and expected configuration output. Integration tests can exercise a device simulator. System tests can run approval, deployment, and validation as one workflow. A limited production canary can confirm behavior against low-risk devices before full rollout.

### 9.2 Reviews and Layered Testing

A professional review considers requirement fit, architectural consistency, correctness, error handling, security, maintainability, performance, and supportability. Network automation adds questions about target scope, idempotency, rate limits, partial failure, rollback, and proof of success. Peer, architecture, security, and stakeholder reviews offer different perspectives and should be used according to change risk.

Testing supplies repeatable evidence. Unit tests isolate calculations and validation; contract tests detect incompatible API changes; integration tests exercise databases, queues, and controller sandboxes; system tests follow the complete workflow; and acceptance tests connect results to user requirements. If a workflow creates a VLAN, one test rejects reserved IDs, another validates the REST payload, another creates the VLAN in a lab, and an end-to-end test confirms client connectivity. A resilience test can then interrupt the response and verify that the workflow finds the existing controller task instead of creating a duplicate.

### 9.3 Conducting an Effective Review

An effective review begins with context. The author should explain the problem, intended behavior, important design choices, risk, testing, and rollback. Reviewers can then focus on whether the solution is correct rather than reverse-engineering its purpose from a large diff. Small, coherent changes receive deeper review than submissions that mix refactoring, formatting, new behavior, and dependency upgrades.

Comments should be specific and constructive. “This is wrong” provides little guidance; “this retry can submit the non-idempotent POST twice after a read timeout” identifies both the defect and its consequence. Teams should distinguish required corrections from optional suggestions and record significant architectural decisions outside the pull-request conversation so they remain discoverable.

### 9.4 Testing Failure, Not Only Success

The happy path is usually the easiest behavior to implement. Production failures occur when DNS is slow, a token expires between pages, a controller returns malformed data, one device rejects a batch, or the network connection disappears after an operation has started. Tests should therefore exercise uncertainty and partial completion, not only expected responses.

A useful network-automation test environment includes simulators or sandboxes, representative software versions, controlled fault injection, and test identities with realistic permissions. Test data should include empty collections, duplicate names, large inventories, unexpected fields, and sensitive values that must be redacted. Finally, a deployment test should confirm not only that the application starts, but that it can reach its queue, secret service, database, controller, and required device networks.

Testing is strongest when failures lead to better design. If a timeout test cannot determine whether a remote task began, the interface may need an idempotency key or reconciliation step. If rollback cannot restore service after a schema migration, the release strategy may need expand-and-contract compatibility. In this way, testing does more than find defects; it exposes architectural assumptions before production does.

## 10. Sequence Diagrams for API Workflows

Sequence diagrams show interactions in time order and make synchronous calls, events, errors, and trust boundaries visible.

```mermaid
sequenceDiagram
    autonumber
    actor Engineer
    participant UI as Automation UI
    participant API as Change API
    participant Auth as Identity Service
    participant Q as Job Queue
    participant Worker
    participant Device

    Engineer->>UI: Submit approved change
    UI->>API: POST /v1/changes
    API->>Auth: Validate identity and permission
    Auth-->>API: Claims
    API->>Q: Publish change task
    API-->>UI: 202 Accepted + job ID
    Q-->>Worker: Deliver task
    Worker->>Device: Apply candidate configuration
    Device-->>Worker: Commit result
    Worker->>Device: Verify intended state
    Worker-->>API: Store completion status
    UI->>API: GET /v1/jobs/{id}
    API-->>UI: Completed result
```

The diagram reveals design questions: whether submission is idempotent, how long authentication may take, what happens when the device commits but the worker loses connectivity, how duplicate delivery is handled, and which identifiers connect telemetry across participants.

## 11. Requirements Engineering in Practice

Requirement discovery is iterative. Stakeholders often describe a desired feature without identifying data ownership, failure behavior, authorization, scale, or operational impact. The development team turns that broad intent into a collection of testable statements.

A useful discovery sequence begins with the business outcome and identifies actors, triggers, inputs, normal behavior, alternate behavior, outputs, and downstream effects. A request to “automate branch deployment” expands into questions about inventory source, device identity, address allocation, controller availability, approval, retries, rollback, and evidence of success.

### 11.1 Requirement Categories

Business requirements explain why the system exists. User requirements describe results that operators and consumers need. Administrative requirements cover identity, policy, audit, retention, and routine support. System requirements identify software, hardware, interface, and protocol behavior.

```mermaid
flowchart TB
    Business["Business outcome"] --> User["User capabilities"]
    Business --> Admin["Governance and administration"]
    User --> System["System behavior and interfaces"]
    Admin --> System
    System --> Tests["Acceptance and quality tests"]
```

A single requirement should address one behavior and should identify the responsible actor. “The application shall discover devices, configure them, and produce reports” combines several independently testable capabilities. Separating them permits different priorities and delivery iterations.

Negative requirements are equally important. A network change service shall not deploy an unapproved candidate, reveal credentials, continue after failed prechecks, or apply a template to an unsupported platform.

### 11.2 Traceability

Traceability connects a business need to requirements, design elements, code, tests, and release evidence. When a security policy changes, the team can identify affected interfaces and tests. When a test fails, the team can identify the requirement at risk.

| Trace item | Network automation content |
|---|---|
| Business need | Reduce branch activation time without reducing control |
| Functional requirement | Create a branch deployment job from approved site data |
| Quality requirement | Complete 95 percent of deployments within 20 minutes |
| Design element | Job API, queue, regional worker, controller adapter |
| Verification | Contract, integration, performance, and rollback tests |
| Operational evidence | Job events, configuration diff, post-change validation |

## 12. Architecture Documentation and Decision-Making

No single diagram can describe an entire architecture. Teams need views suited to different questions:

- A context view shows users, external systems, and trust boundaries.
- A component view shows responsibilities and interfaces.
- A deployment view maps components to processes, hosts, clusters, or regions.
- A data-flow view shows creation, movement, storage, and retention.
- A sequence view shows runtime interaction and timing.

Architecture decision records capture a decision, context, alternatives, consequences, and status. The value lies in preserving why the team chose a queue instead of a synchronous call, a modular monolith instead of microservices, or a controller API instead of direct device access.

Documentation must evolve with the implementation. A stale architecture diagram is worse than a visibly incomplete one because it creates false confidence. Automated generation can help inventory deployed components, but it does not replace explanations of intent and trade-offs.

## 13. Testing Strategy Across the Delivery Lifecycle

A test strategy balances speed, isolation, and realism.

```mermaid
flowchart TB
    Unit["Many fast unit tests"] --> Contract["API and schema contract tests"]
    Contract --> Integration["Integration tests with controlled dependencies"]
    Integration --> System["End-to-end system tests"]
    System --> Acceptance["Limited acceptance and production verification"]
```

Unit tests can validate template selection, parsing, and policy evaluation without a network. Contract tests verify OpenAPI, event, or YANG expectations. Integration tests exercise databases, queues, controllers, and device simulators. System tests run the complete approval and deployment workflow. Production verification should be small, observable, and reversible.

Test data needs the same care as production data. Captured device output may contain addresses, usernames, keys, or customer identifiers and should be sanitized. Simulators should include slow responses, malformed payloads, disconnections, partial success, and unsupported capability rather than only ideal behavior.

Automated tests reduce regression risk but cannot prove that every operational condition is safe. Architecture review, threat modeling, load testing, failure injection, and staged deployment address risks that ordinary functional tests miss.

## 14. Delivery Models and Organizational Fit

Waterfall provides value when scope is stable, formal approval is mandatory, and later change is rare. Agile methods are effective when feedback and requirements evolve. Most organizations combine elements: annual architecture and budget planning, iterative product delivery, continuous integration, and controlled production change windows.

Scrum uses a prioritized backlog, time-boxed sprint, review, and retrospective. Kanban limits work in progress and reveals flow constraints. Extreme Programming emphasizes practices such as automated tests, simple design, refactoring, and close feedback. Lean asks whether each activity creates customer value and encourages the team to optimize the complete system rather than one local step.

The development model does not eliminate operational responsibilities. A sprint that ends with unreviewed code is not a finished increment. The definition of done should include tests, documentation, security checks, packaging, deployment readiness, and relevant telemetry.

## 15. End-to-End Architecture Walkthrough

Consider a platform that validates and remediates network configuration. Its purpose is not simply to send commands. It must translate business policy into controlled actions and preserve evidence.

The workflow begins when policy owners define an approved standard. The inventory service identifies devices, sites, roles, platform families, and management endpoints. Collectors retrieve operational and configuration state through controller APIs, NETCONF, RESTCONF, or other approved interfaces. Parsers normalize vendor-specific data into an internal model. The policy engine compares observed state with desired state and produces findings.

An operator selects findings for remediation. The application verifies scope, approval, maintenance window, device reachability, and rollback capability. It renders candidates and stores immutable previews. A durable queue separates submission from execution. Workers apply bounded concurrency so a controller or device management plane is not overwhelmed.

Post-change validation confirms intended state and checks for negative effects. A job is complete only when execution and verification reach a terminal outcome. Audit records connect user identity, approval, code version, template version, input data, device result, and timestamps.

```mermaid
flowchart LR
    Policy["Approved policy"] --> Assess["Collect and assess"]
    Inventory["Device inventory"] --> Assess
    Assess --> Findings["Compliance findings"]
    Findings --> Approval["Scope and approval"]
    Approval --> Render["Render and preview"]
    Render --> Queue["Durable job queue"]
    Queue --> Deploy["Controlled deployment"]
    Deploy --> Validate["Post-change validation"]
    Validate --> Audit["Evidence and audit"]
```

Each stage exposes a contract. Inventory does not need to understand template syntax. The renderer does not need device credentials. Approval logic does not open sessions. These boundaries support testability and independent change even when the application remains one deployment.

Failure behavior is part of architecture. If collection fails, the system records unknown state rather than assuming compliance. If approval expires, execution stops. If the device commits but the response is lost, the worker checks observed state before retrying. If validation fails, the workflow follows a defined rollback or escalation policy.

## 16. Security Throughout the Lifecycle

Security requirements apply to design, implementation, delivery, and operation.

Threat modeling identifies assets, trust boundaries, entry points, abuse cases, and controls. In an automation platform, important assets include credentials, configuration, inventory, approval records, software artifacts, and the ability to alter production devices.

Controls include:

- Strong workload and user identity
- Least-privilege authorization
- Secret storage and rotation
- TLS with certificate validation
- Input and schema validation
- Output encoding and log redaction
- Dependency and artifact scanning
- Signed or attested releases
- Tamper-resistant audit records
- Rate and concurrency limits

Security tests should verify denied behavior as well as permitted behavior. A read-only user must not create a change by calling the API directly. A worker credential for one tenant must not access another. A template field must not inject arbitrary commands.

Defense in depth assumes one control can fail. Even after the UI hides a button, the API enforces permission. Even after the API validates scope, the worker receives narrowly scoped credentials. Even after the worker succeeds, post-change validation detects unexpected state.

> **Study guide takeaway:** When evaluating an automation design, trace one change from user intent to post-change verification. If you cannot identify the owner of state, the trust boundaries, the failure path, and the evidence of success, the design is not yet complete.

## Key Takeaways

- Distributed applications separate front-end interaction, back-end logic, data, execution, and telemetry across cooperating components.
- Requirements, constraints, and quality attributes guide the choice among monolithic, service-oriented, microservices, and event-driven architectures.
- The SDLC, DevOps, reviews, testing, and sequence diagrams turn code into dependable operational software.

With the software-development foundation established, Chapter 2 examines the quality attributes that determine whether an application is trustworthy in production.

## Further Reading and References

- [The Twelve-Factor App](https://12factor.net/) - principles for portable service design.
- [Mermaid sequence diagrams](https://mermaid.js.org/syntax/sequenceDiagram.html) - syntax for documenting API interactions.

**Next chapter:** [Chapter 2: Software Quality and Resilience](Chapter2.md)
