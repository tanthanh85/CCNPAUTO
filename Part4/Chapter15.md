# Chapter 15: Edge Application Hosting

## Chapter Introduction

Edge computing places selected processing near users, devices, and data sources. Cisco application hosting allows containerized workloads to run on supported Catalyst 9000 and IOx-enabled platforms. This chapter explains the benefits, constraints, deployment workflow, networking, security, and lifecycle management of those applications.

## 1. Why Compute at the Edge?

Central cloud platforms offer elasticity and operational consistency, but sending every event to a distant data center can add latency, consume WAN bandwidth, and conflict with data-location requirements.

```mermaid
flowchart LR
    Sensors["Users, sensors, and local systems"] --> Edge["Cisco edge device with hosted app"]
    Edge --> Local["Immediate local analysis or action"]
    Edge -->|filtered summaries| Cloud["Central cloud or data center"]
    Cloud --> Fleet["Fleet policy and analytics"]
```

An edge application can normalize industrial data, filter telemetry, run a local protocol gateway, perform site health checks, or maintain limited function during WAN loss. It should not be placed on a network device merely because it can be. Protect the primary forwarding role and verify resource and support boundaries.

## 2. Virtual Machines and Containers

A virtual machine includes a guest operating system and virtual hardware. A container packages an application and dependencies while sharing the host kernel. Containers usually start faster and consume fewer resources, but kernel isolation is not identical to a VM boundary.

```mermaid
flowchart TB
    subgraph VMHost["Virtual-machine host"]
      HV["Hypervisor"] --> VM1["Guest OS + application"]
      HV --> VM2["Guest OS + application"]
    end
    subgraph ContainerHost["Container host"]
      OS["Host OS / kernel"] --> C1["App container"]
      OS --> C2["App container"]
    end
```

Type 1 hypervisors run directly on hardware; Type 2 hypervisors run on a host OS. Cisco edge platforms vary: some support containers, virtual machines, or IOx application packages. Always consult the exact platform and software release documentation.

## 3. Cisco Application-Hosting Platforms

Cisco IOx combines network operating capabilities with an application environment on supported industrial routers, gateways, and other edge products. Supported Catalyst 9000 switches can host applications through IOS XE application-hosting features. Some NX-OS platforms support container environments for appropriate operational use cases.

Capability is platform-, license-, architecture-, and release-specific. Confirm CPU architecture, memory, storage, container format, interfaces, orchestration support, and lifecycle commands before selecting a target.

## 4. Application Architecture

```mermaid
flowchart TB
    Mgmt["Management / deployment system"] --> IOSXE["Cisco IOS XE"]
    IOSXE --> Runtime["Application-hosting runtime"]
    Runtime --> App["Containerized application"]
    App --> AppGig["AppGigabitEthernet interface"]
    AppGig --> VLAN["VLAN or routed network"]
    App --> Storage["Allocated persistent storage"]
    App --> Logs["Logs and health status"]
```

The hosted application receives explicitly allocated CPU, memory, storage, and network connectivity. On IOS XE, an AppGigabitEthernet interface links the application environment to the switch networking context. VLAN, addressing, routing, DNS, and access policy must be designed just like any other workload.

## 5. Building the Image

Build a minimal image for the target CPU architecture. Pin dependencies, run as a non-root user, include a health check, write logs to standard output where supported, and keep mutable data outside the image.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY edge_collector.py .
USER 10001
CMD ["python", "edge_collector.py"]
```

Scan the image for known vulnerabilities, produce a software bill of materials, sign the approved image, and record its digest. A tag such as `latest` is not a reproducible release identity.

## 6. Deployment Lifecycle

```mermaid
flowchart LR
    Build["Build and test image"] --> Package["Package for target platform"]
    Package --> Transfer["Transfer or register image"]
    Transfer --> Install["Install application"]
    Install --> Configure["Allocate resources and network"]
    Configure --> Activate["Activate/start"]
    Activate --> Verify["Verify app and network health"]
    Verify --> Manage["Monitor, upgrade, or uninstall"]
```

For IOS XE application hosting, the operational sequence generally includes defining the application ID, configuring resource and interface settings, installing the package, activating it, starting it, and inspecting status. Exact syntax changes by platform and release, so automation should discover or validate capabilities.

Image transfer can use a supported local or remote repository. Deployment may be performed through CLI, IOx Local Manager for a single device, Cisco Catalyst Center for supported fleet workflows, or IOx management APIs and tools.

## 7. Networking the Hosted Application

Plan whether the application needs management access, production data, local sensors, or internet services. Apply least-privilege ACLs and segmentation. Avoid bridging an untrusted sensor network directly into the management plane.

```mermaid
flowchart LR
    OT["Local OT / sensor VLAN"] -->|required ports only| App["Edge application"]
    App -->|HTTPS / telemetry| Central["Central service"]
    Admin["Management network"] -->|deployment and monitoring| Host["Cisco host device"]
    Host -. isolated control .-> App
```

DNS, NTP, certificate validation, proxy behavior, MTU, and default routing are common sources of deployment failure. Test application traffic after host reload and WAN interruption.

## 8. Security and Resource Protection

Treat an edge container as a production workload:

- Use signed and scanned images from a controlled registry.
- Remove unnecessary packages and Linux capabilities.
- Run without root privileges and use read-only filesystems where possible.
- Inject short-lived secrets at runtime rather than baking them into the image.
- Restrict inbound and outbound connectivity.
- Cap CPU, memory, storage, and log growth.
- Patch the base image and application on a defined schedule.

The host's forwarding and control functions take priority. Load-test the application and define thresholds that stop or throttle it before it affects routing, switching, or controller responsiveness.

## 9. Fleet Operations

Operating one edge application is simple; operating hundreds requires inventory, staged rollout, health reporting, version visibility, certificate rotation, and rollback.

```mermaid
sequenceDiagram
    participant M as Fleet manager
    participant D as Edge device
    participant A as Hosted application
    participant O as Observability platform
    M->>D: Deploy signed image to canary site
    D->>A: Install, activate, and start
    A->>O: Publish health and version
    O-->>M: Confirm service objectives
    M->>D: Expand rollout in bounded batches
```

Monitor both application and host: process health, restarts, CPU, memory, disk, interface traffic, forwarding health, temperature, and WAN reachability. Preserve local buffering limits for disconnected operation and define what happens when storage fills.

## 10. Selecting an Edge Workload

A strong edge use case benefits from low latency, local autonomy, bandwidth reduction, protocol locality, or data sovereignty. A weak use case requires large elastic compute, depends on many cloud services, grows storage unpredictably, or risks competing with critical network functions.

## 11. Edge Architecture and Failure Behavior

The main architectural advantage of edge computing is not simply geographical proximity; it is the ability to make a useful decision inside the local failure domain. A manufacturing gateway can continue translating sensor protocols and enforcing safe thresholds when the WAN is unavailable. A retail application can buffer transactions locally and synchronize when connectivity returns. The application must therefore define which operations are safe offline, how long data may be buffered, how conflicts are resolved, and what happens when local storage reaches its limit.

Local autonomy also creates distributed-state challenges. Hundreds of sites may run different application versions, certificate generations, or cached policy if fleet management is weak. Desired state should identify the image digest, configuration version, resource allocation, and certificate profile for every deployment group. Devices report actual state, allowing the manager to detect drift and stage remediation.

```mermaid
flowchart TD
    Desired["Fleet desired state"] --> Compare["Compare reported app state"]
    Report["Version, health, resources, certificate age"] --> Compare
    Compare -->|compliant| Observe["Continue monitoring"]
    Compare -->|drift| Risk["Classify risk and connectivity"]
    Risk --> Canary["Update canary device"]
    Canary --> Verify["Verify app and host health"]
    Verify --> Rollout["Roll out in bounded groups"]
```

## 12. Packaging and Platform Compatibility

Container portability has limits. An image built for x86-64 will not run on an ARM target unless a corresponding image is built. Kernel features, device access, storage drivers, and runtime versions also differ. Multi-architecture build pipelines can produce platform-specific images under one manifest, but each target still requires testing.

IOx applications may use Cisco packaging metadata to declare resources, startup behavior, networking, and application properties. Docker images for supported Catalyst application hosting must comply with platform requirements and be transferred in a supported form. The exact workflow varies across IOS XE releases, which is why a deployment system should maintain a platform compatibility matrix rather than assume one package works everywhere.

Persistent data must be treated separately from the replaceable image. An upgrade should not unexpectedly destroy buffered telemetry, databases, or locally issued certificates. At the same time, unlimited persistent data can fill device storage and affect the host. Define quotas, retention, export, backup, and cleanup behavior explicitly.

## 13. Operational Troubleshooting

Troubleshooting proceeds from host to runtime to application to network. First confirm that the platform supports application hosting and has sufficient resources. Then inspect installation, activation, and running state. Review application logs and exit status. Finally, test the AppGigabitEthernet path, VLAN or routing, DNS, NTP, TLS trust, firewall policy, and remote-service reachability.

A container can be running while the service is unusable. Health checks should verify meaningful dependencies without becoming destructive or overly expensive. A liveness check determines whether the process should restart. A readiness check determines whether it should receive traffic. If the application depends on a central API, decide whether temporary API failure should make the local application unready or whether degraded offline behavior remains useful.

Resource exhaustion requires correlation. High application CPU may be legitimate processing, an application defect, or hostile input. Storage growth may come from buffered events or uncontrolled logs. Monitor the network device control plane and forwarding health alongside the container so operators can stop the workload before it threatens the primary network function.

## 14. Secure Fleet Lifecycle

Supply-chain controls begin before deployment. The pipeline should build from approved base images, pin dependencies, scan code and packages, generate an SBOM, sign the image, and publish it to a controlled registry. The deployment platform verifies provenance and digest before installation. Runtime configuration supplies environment-specific endpoints and short-lived secrets.

Patch policy must account for intermittently connected sites. Critical updates may need staged distribution and local scheduling. Certificate rotation should begin well before expiration and tolerate temporary clock or WAN issues without disabling identity validation. When a device or application is retired, revoke credentials, remove it from fleet inventory, export required evidence, and securely erase sensitive data.

Rollbacks should use a previously approved immutable image and compatible configuration. Database or data-format migrations can make rollback impossible unless the application supports backward compatibility or preserves a recovery snapshot. This is another reason to test upgrade and rollback as a pair rather than treating rollback as a line in a runbook.

## 15. Cisco IOx Application Model

Cisco IOx provides a framework for packaging, deploying, and managing applications on supported edge platforms. The platform combines the networking functions of the device with an isolated application environment. Applications interact with explicitly assigned interfaces and resources rather than receiving unrestricted access to the network operating system. This boundary is central to the design: application innovation should not compromise forwarding stability or the integrity of IOS XE.

An IOx package contains the application artifacts and metadata required by the platform. Depending on target capability, the workload may be a container or virtual-machine style package. Metadata declares resource requirements, startup commands, networking, and application properties. The package should be built for the target architecture and validated against platform-specific limits before distribution.

IOx Local Manager is useful for managing applications on an individual device through a local interface. Broader fleets require centralized systems and APIs. Cisco Catalyst Center can support application-hosting workflows on appropriate Catalyst platforms, while IOx management tools and APIs serve supported edge families. The exact available method depends on device model, IOS XE release, licenses, and deployment architecture.

## 16. IOS XE Application-Hosting Workflow

On a supported Catalyst platform, an application is identified by an application ID. Configuration associates resources, virtual interfaces, VLAN or management connectivity, and optional storage. Operational commands install the package, activate its resources, start the application, and expose status or logs. The states matter: an application can be installed but not activated, activated but not running, or running but unhealthy.

```text
Package prepared and transferred
        |
        v
Install -> Activate -> Start -> Verify
   |          |          |        |
 files     resources   process   service outcome
```

The engineer should capture prechecks before installation: platform support, available flash or application storage, CPU and memory capacity, AppGigabitEthernet availability, VLAN and routing dependencies, DNS/NTP, and certificate trust. Activation can fail if requested resources cannot be reserved. Startup can fail because of an incorrect command, missing dependency, architecture mismatch, permission problem, or unavailable network service.

Automation should poll application state rather than assume that a CLI or API acknowledgement represents completion. After startup, verify the process, health endpoint, logs, network path, and host health. If the application provides a local data service, test a representative transaction. Record the deployed image digest and configuration version in fleet inventory.

## 17. Network Integration Patterns

A hosted application can use a dedicated VLAN, a routed application interface, or platform-supported management connectivity. The selection determines reachability and policy. A telemetry collector that communicates only with local devices and a central broker does not require unrestricted campus access. An industrial protocol gateway may require one interface toward an OT segment and another controlled path toward central services, with firewall policy preventing it from becoming a general bridge.

IP addressing can be static or supplied through a local service, depending on platform and application requirements. Static addressing simplifies predictable inbound access but increases fleet address management. Dynamic addressing reduces per-device configuration but requires reliable DNS or service discovery. In either case, maintain a source of truth that associates application identity, host device, site, address, certificate, and version.

MTU and fragmentation deserve attention when applications encapsulate telemetry or use VPN paths. DNS and NTP are foundational: name-resolution failure can appear to be an API outage, and incorrect time breaks certificates and event ordering. Proxy requirements, certificate authorities, and outbound firewall rules should be included in the application profile rather than discovered during deployment.

## 18. Edge Data and Offline Operation

Edge applications often exist because connectivity is constrained, so offline behavior is a primary design requirement. The application should use a bounded local queue, persist only necessary data, and assign sequence identifiers so the central service can detect duplicates and gaps after reconnection. Backpressure determines what happens when producers generate data faster than it can be stored or transmitted.

Not all data has equal value. The application may aggregate high-frequency raw readings into summaries while preserving fault events at full fidelity. It can discard repetitive healthy samples before sending them over a metered WAN. These choices should be documented because local filtering changes what central analysts can later investigate.

Synchronization must be idempotent. If an upload succeeds but the acknowledgement is lost, resending the same batch should not create duplicate business records. The central API can use batch IDs or idempotency keys, and the edge application should delete local data only after durable acknowledgement. Encryption at rest may be necessary because a physically remote device can be lost or tampered with.

## 19. Application Observability at the Edge

Logs, metrics, traces, and health state must operate under constrained bandwidth. Local logs should use structured records, timestamps, severity, and correlation IDs, with rotation and size limits. Critical events can be forwarded immediately, while verbose diagnostic logs remain local for a bounded period. Secrets and personal data should never be written merely because the site is remote.

Metrics should distinguish application demand from resource saturation. Queue depth, processing latency, dropped events, synchronization age, API failures, restart count, CPU, memory, and disk provide a useful baseline. Host metrics reveal whether the workload affects the switch or router. A central dashboard should show version and certificate age as well as health so maintenance risks are visible before an outage.

Distributed tracing may be too expensive for every edge request, but sampled correlation across edge, WAN, and cloud can explain latency. When the central service receives a batch, retaining the edge-generated correlation or batch ID makes it possible to follow the transaction without collecting every internal detail.

## 20. Choosing Between Edge, Cloud, and Hybrid Deployment

Edge is appropriate when local latency, autonomy, bandwidth cost, protocol access, or data sovereignty materially improves the service. Cloud is appropriate when workloads need elastic compute, centralized data, frequent software evolution, or rich managed services. Hybrid designs commonly perform filtering and immediate action at the edge while sending summaries to central analytics and fleet management.

The decision should consider the total operating model. A cloud service may be technically distant but far easier to patch, observe, and scale. An edge application may save bandwidth but create hundreds of small production environments. Quantify WAN savings, latency, outage behavior, hardware resource cost, support travel, security exposure, and fleet-management effort.

> **Study guide takeaway:** Application hosting turns a network platform into a carefully shared edge-compute environment. Success depends on selecting the right workload and protecting the device's primary networking responsibility through isolation, resource limits, secure images, and fleet lifecycle management.

## Key Takeaways

- Edge computing supports low latency, local autonomy, bandwidth reduction, protocol locality, and data-location requirements.
- Cisco IOx and supported Catalyst platforms can host carefully isolated containerized applications near users and devices.
- Secure fleet operations require compatible images, controlled resources, network policy, observability, staged upgrades, offline behavior, and tested rollback.

Chapter 16 concludes the guide by applying the accumulated design and automation skills to major Cisco platform APIs and SDKs.

## Further Reading and References

- [Cisco IOx documentation](https://developer.cisco.com/docs/iox/) - application packaging and edge deployment.
- [Docker documentation](https://docs.docker.com/) - container images and runtime concepts.
- [Cisco application-hosting resources](https://developer.cisco.com/site/iox/) - Cisco edge application development resources.
