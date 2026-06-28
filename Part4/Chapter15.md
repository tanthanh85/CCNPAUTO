# Chapter 15: Hosting Applications on Network Devices

## Chapter Purpose

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

AI inference at the edge can classify events without sending raw data centrally, but model size, accelerator availability, power, privacy, update integrity, and drift monitoring must be considered. Training generally belongs on centralized compute; the edge is better suited to bounded inference.

> **Study guide takeaway:** Application hosting turns a network platform into a carefully shared edge-compute environment. Success depends on selecting the right workload and protecting the device's primary networking responsibility through isolation, resource limits, secure images, and fleet lifecycle management.

## Chapter Summary

Edge computing reduces latency and WAN dependence while supporting local autonomy and data-location needs. Containers package applications efficiently, and Cisco IOx and supported Catalyst platforms provide hosting capabilities. Deployment must address image integrity, networking, resources, observability, upgrades, and rollback across the fleet.
