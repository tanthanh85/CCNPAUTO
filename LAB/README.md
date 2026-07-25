# CCNPAUTO Lab Guide

## Lab Guide Introduction

This lab series is the practical companion to the CCNPAUTO study guide. The theory chapters explain software design, APIs, deployment, security, infrastructure automation, Cisco platforms, and AI-assisted network operations. The labs apply those subjects to a working environment and a cumulative enterprise network automation project.

The course begins with a single Ubuntu workstation and gradually builds toward a professional automation workflow. Learners first prepare the required tools and validate device access. They then create a GitLab.com project, move from file-based intent to NetBox, protect credentials with Vault, configure IOS XE through CLI and model-driven interfaces, automate the workflow with GitLab CI/CD, migrate orchestration to Ansible, add resilience and observability, containerize the runtime, collect model-driven telemetry, detect drift, and finally build an AI route assistant that uses FastMCP and RESTCONF.

The labs are written for learners who already have CCNA Automation knowledge. Therefore, they do not reteach introductory Python, Git, structured data, or REST API fundamentals. Instead, they extend those foundations to CCNP-level work in which an engineer must validate intent, protect credentials, control deployment, verify operational state, preserve evidence, and troubleshoot failures.

## Required Prior Knowledge

Before beginning the lab series, learners should be able to:

- Explain routing, switching, IP addressing, VLAN, and OSPF concepts at approximately CCNA level.
- Read and modify straightforward Python programs that use variables, functions, classes, loops, conditionals, and exception handling.
- Work with lists, dictionaries, environment variables, modules, and Python virtual environments.
- Read and edit JSON, YAML, and XML data.
- Explain HTTP methods, headers, status codes, authentication, and basic REST API behavior.
- Perform common Git operations, including cloning, branching, committing, merging, and pushing to a remote repository.
- Describe the purpose of CLI automation, RESTCONF, NETCONF, YANG, and controller APIs.

The instructions still provide the commands, file locations, and verification points required for the course. However, learners are expected to interpret results and troubleshoot their work rather than treat each task as an introductory programming exercise.

## Recommended Lab Order

Follow the labs in order unless the instructor explicitly says otherwise. Labs 3–13 are cumulative and use the same main project repository, so skipping one may leave missing modules, variables, services, or pipeline files. Lab 14 is a separate AI application that consumes network information through a controlled MCP service.

```mermaid
flowchart TD
    L1["Lab 1<br/>Prepare workstation"] --> L2["Lab 2<br/>Warm-up access"]
    L2 --> L3["Lab 3<br/>Start project with YAML"]
    L3 --> L4["Lab 4<br/>Move intent to NetBox"]
    L4 --> L5["Lab 5<br/>Move secrets to Vault"]
    L5 --> L6["Lab 6<br/>Add NETCONF OSPF"]
    L6 --> L7["Lab 7<br/>NetBox-triggered CI/CD"]
    L7 --> L8["Lab 8<br/>Migrate orchestration to Ansible"]
    L8 --> L9["Lab 9<br/>Add API resilience"]
    L9 --> L10["Lab 10<br/>Logging and observability"]
    L10 --> L11["Lab 11<br/>Containerized runtime"]
    L11 --> L12["Lab 12<br/>Model-driven telemetry"]
    L12 --> L13["Lab 13<br/>Drift and compliance"]
    L13 --> L14["Lab 14<br/>AI route assistant"]
    L14 --> F["Final Assessment<br/>Two practical projects"]
```

## Repository Flow

The labs use GitLab.com for repositories and pipeline coordination.

| Repository | Used by | Purpose |
|---|---|---|
| `lab2_warm_up` | Lab 2 | Disposable warm-up repository used to confirm Git, Python, DevNet VPN, CLI parsing, and RESTCONF access. |
| `network_automation_project` | Labs 3–13 | Main cumulative automation project. Learners keep improving this repository across multiple labs. |
| `ai_route_assistant` | Lab 14 | Separate Flask and FastMCP assistant using local Ollama or an OpenAI/Anthropic API. |

This separation keeps the warm-up and AI assistant independent from the main production-style automation project. The main project remains focused on source-of-truth-driven network changes, CI/CD, Ansible, observability, and compliance.

## Lab Summary

### Lab 1: Preparing the Network Automation Workstation

[Lab 1](Lab1/Lab1.md) prepares the Ubuntu 26.04 workstation used throughout the course. Learners install Python tooling, network automation libraries, Ansible, Terraform, Docker, NetBox, Vault, Git, Visual Studio Code, and GitLab Runner. Learners may deploy TIG and Cisco YANG Suite locally or use the Cisco DevNet Sandbox TIG and YANG Suite services. NetBox remains the local source of truth, while Vault provides secrets for later automation.

This is the foundation lab. If a later lab fails because a service is missing, a Python package is unavailable, or a runner is not registered, return to Lab 1 and verify the workstation.

### Lab 2: Network Automation Warm-Up

[Lab 2](Lab2/Lab2.md) confirms that the learner can use GitLab.com, Python virtual environments, a Cisco DevNet IOS XE reservable sandbox, Netmiko, TextFSM, and RESTCONF. The lab intentionally uses a separate repository named `lab2_warm_up` because it is a readiness check rather than part of the main project.

Learners retrieve `show version` and `show ip interface brief`, parse CLI output, and display the results as tables. They then use Postman to inspect a RESTCONF request manually before consuming the same structured YANG JSON in Python. This comparison shows why structured APIs become increasingly valuable as automation grows.

### Lab 3: Start the Network Automation Project

[Lab 3](Lab3/Lab3.md) begins the cumulative repository named `network_automation_project`. Learners define loopback interfaces in YAML, validate the source of truth, render IOS XE configuration with Jinja2, apply the configuration with Netmiko, and verify the resulting device state.

This lab introduces the first version of the automation workflow:

```mermaid
flowchart LR
    YAML["YAML loopback intent"] --> Validate["Validate input"]
    Validate --> Render["Render Jinja2 config"]
    Render --> Apply["Apply with Netmiko"]
    Apply --> Verify["Verify IOS XE state"]
```

The YAML file is useful for learning because it is easy to read and version in Git. However, it has limited relationships, API capability, and operational governance. Lab 4 improves that by moving intent to NetBox.

### Lab 4: Move the Source of Truth to NetBox

[Lab 4](Lab4/Lab4.md) replaces the active YAML source of truth with NetBox. Learners model the IOS XE sandbox router, create loopback virtual interfaces, assign `/32` IP addresses, tag managed objects, and retrieve intent through the NetBox REST API.

The automation still reuses the validation, Jinja2, Netmiko, and verification ideas from Lab 3. The main change is the source of truth:

```mermaid
flowchart LR
    NetBox["NetBox device, interfaces,<br/>IP addresses, tags"] --> API["NetBox REST API"]
    API --> Automation["Network automation project"]
    Automation --> IOSXE["IOS XE sandbox"]
```

NetBox becomes important because later labs need an authoritative inventory and intent system that can trigger automation.

### Lab 5: Manage Credentials with HashiCorp Vault

[Lab 5](Lab5/Lab5.md) moves IOS XE credentials out of `.env` and into HashiCorp Vault. The project continues to use the same device clients, but the settings layer now retrieves secrets from Vault rather than from local files.

This lab reinforces a key production habit: ignoring a file in Git is not the same as managing a secret. Vault gives learners a safer pattern for storing and retrieving credentials, while also teaching why development-mode Vault is not production-ready.

### Lab 6: Configure OSPF with NETCONF and YANG

[Lab 6](Lab6/Lab6.md) adds model-driven configuration to the project. Learners use local Cisco YANG Suite or Cisco DevNet Sandbox YANG Suite at `http://10.10.20.50:8480` to inspect IOS XE native YANG models, build an OSPF payload, render XML with Jinja2, and send an `<edit-config>` operation through NETCONF. The lab advertises all managed loopback interfaces into OSPF area 0.

This lab is where learners begin to connect source of truth, secret management, and model-driven programmability:

```mermaid
flowchart LR
    NetBox["Loopback intent"] --> Project["Python project"]
    Vault["IOS XE credentials"] --> Project
    Project --> XML["Cisco IOS XE native<br/>YANG XML payload"]
    XML --> NETCONF["NETCONF edit-config"]
    NETCONF --> Router["IOS XE router"]
```

The important lesson is that model-driven automation requires checking the device-advertised model, not blindly trusting a sample payload.

### Lab 7: Trigger Automation from NetBox with GitLab CI/CD

[Lab 7](Lab7/Lab7.md) connects the individual components into an event-driven workflow. A NetBox event rule triggers a GitLab.com pipeline. The local GitLab Runner validates NetBox intent, retrieves credentials from Vault, configures loopbacks, configures OSPF, verifies IOS XE state, and stores artifacts.

The webhook does not carry trusted configuration by itself. It only signals that intent may have changed. The pipeline re-reads NetBox as the authoritative source of truth before making changes.

```mermaid
flowchart LR
    Admin["Admin updates NetBox"] --> Webhook["NetBox webhook"]
    Webhook --> GitLab["GitLab.com pipeline"]
    GitLab --> Runner["Local GitLab Runner"]
    Runner --> NetBox["Read current intent"]
    Runner --> Vault["Read credentials"]
    Runner --> Router["Configure and verify IOS XE"]
    Runner --> Artifacts["Store evidence"]
```

### Lab 8: Migrate Orchestration from Python to Ansible

[Lab 8](Lab8/Lab8.md) keeps the same operating model from Lab 7 but migrates orchestration from custom Python jobs to Ansible playbooks. NetBox still provides intent, Vault still provides credentials, GitLab CI/CD still triggers the workflow, and IOS XE remains the target.

This lab helps learners compare Python and Ansible realistically. Python offers precise application logic. Ansible offers readable task execution, network modules, collections, check mode, diff behavior, and familiar operational reports. The lab shows that tooling changes do not remove the need for validation, secret handling, and verification.

### Lab 9: Add API Resilience

[Lab 9](Lab9/Lab9.md) improves the project’s behavior when APIs are unreliable. Learners add bounded retry logic, timeouts, exponential backoff, jitter, and `Retry-After` handling. The lab distinguishes recoverable failures such as temporary `5xx` responses from unrecoverable problems such as invalid credentials or malformed requests.

This lab matters because real automation depends on other systems. NetBox, Vault, controllers, and devices can all be slow or temporarily unavailable. A professional automation workflow fails clearly, retries carefully, and avoids infinite loops.

### Lab 10: Add Application Logging and Observability

[Lab 10](Lab10/Lab10.md) adds structured JSON Lines audit events, GitLab artifacts, InfluxDB metrics, and Grafana dashboards. Learners observe who triggered automation, which tasks ran, how long they took, what changed, and where failures occurred.

This lab separates three ideas:

- human-readable job output,
- structured audit records,
- and time-series metrics.

That separation is important because troubleshooting one failed pipeline and understanding long-term automation reliability require different kinds of evidence.

### Lab 11: Containerize the Automation Runtime

[Lab 11](Lab11/Lab11.md) packages the Ansible runtime into a Docker image. Instead of rebuilding the environment from scratch during every pipeline, the project uses a consistent container image containing pinned Python dependencies and Ansible collections.

Containerizing the runtime improves repeatability. The source code remains in Git, secrets remain outside the image, and the pipeline runs with a known set of tools. This prepares learners for production practices where automation jobs run in controlled execution environments.

### Lab 12: Add Model-Driven Telemetry

[Lab 12](Lab12/Lab12.md) shifts attention from the automation application to the network device itself. Learners use YANG Suite to locate operational data paths, examine dial-in collection through NETCONF and gNMI, and configure Catalyst C8KV IOS XE to push CPU, memory, and interface counter data to Telegraf. The TIG stack stores and visualizes the telemetry.

For gRPC dial-out, learners enter the IOS XE subscriptions manually, beginning with subscription ID 201. Learners using the Cisco Catalyst C8KV sandbox send telemetry to its pre-integrated Telegraf service at `10.10.20.50:57500` and build dashboards in Grafana at `http://10.10.20.50:3000`. Learners using a locally hosted C8KV start the local TIG stack from Lab 1 and send telemetry to the workstation on TCP `57000`.

### Lab 13: Detect Configuration Drift and Report Compliance

[Lab 13](Lab13/Lab13.md) adds a read-only compliance pipeline. The project compares NetBox intent with observed IOS XE loopback and OSPF state, reports drift, and preserves structured evidence without automatically correcting the device.

The lab teaches that drift detection and remediation are different decisions. Sometimes the safest first step is to report clearly rather than repair automatically. This is especially true when multiple teams or systems might touch the same network.

### Lab 14: Build an AI Network Route Assistant

[Lab 14](Lab14/Lab14.md) introduces AI-assisted network operations in a controlled way. Learners build a Flask web assistant with a professional dark theme, select local Qwen through Ollama or an OpenAI or Anthropic API model, expose route-information tools through Python FastMCP, and retrieve live IOS XE route data through RESTCONF behind the MCP server. They compare provider accuracy and response time against the same MCP evidence. If Qwen 8B is too slow for the workstation, a smaller Qwen model can be selected without changing the application architecture.

The key architecture is intentional:

```mermaid
flowchart LR
    Web["Flask web assistant"] --> MCPClient["MCP client abstraction"]
    MCPClient --> MCPServer["FastMCP server"]
    MCPServer --> RESTCONF["RESTCONF"]
    RESTCONF --> IOSXE["IOS XE router"]
    Web --> LLM["Ollama, OpenAI, or Anthropic"]
```

The AI model answers questions from MCP-provided route context. It does not receive router credentials, does not connect directly to IOS XE, and does not execute configuration. This reinforces the Chapter 17 principle that AI belongs behind narrow, controlled, auditable tools.

### Final Assessment Lab: Enterprise Network Automation Delivery

[Final Assessment Lab](FinalLab/README.md) tests learners through two realistic company projects. The first project uses Netmiko and Jinja2 to automate VLAN creation on a Cisco Nexus NX-OS sandbox switch, representing legacy CLI-based devices. The second project uses NETCONF, RESTCONF, local or Cisco DevNet Sandbox YANG Suite, Vault, and Flask to automate static routes and monitor an IOS XE sandbox router, representing modern programmable infrastructure.

The assessment is worth 100 points and includes self-grading scripts so learners can check their completion before submission.

## Main Project Evolution

Labs 3–13 progressively improve the same `network_automation_project` repository.

| Stage | Main Improvement | Operational Lesson |
|---|---|---|
| Lab 3 | YAML intent and Python/Netmiko deployment | Start with a readable workflow and verify results. |
| Lab 4 | NetBox source of truth | Intent belongs in a system that has objects, relationships, API access, and history. |
| Lab 5 | Vault credentials | Secrets should be retrieved from a controlled secret store, not scattered in files. |
| Lab 6 | NETCONF/YANG OSPF configuration | Model-driven interfaces require model discovery and payload validation. |
| Lab 7 | NetBox-triggered GitLab CI/CD | Events should trigger reconciliation against authoritative intent. |
| Lab 8 | Ansible orchestration | Declarative automation still requires validation, secrets, and verification. |
| Lab 9 | API resilience | External dependencies fail; automation must handle timeouts and rate limits safely. |
| Lab 10 | Logging and observability | Operators need evidence, metrics, and retained artifacts. |
| Lab 11 | Containerized runtime | Reproducible execution environments reduce dependency drift. |
| Lab 12 | Model-driven telemetry | Streaming telemetry provides operational visibility into network state. |
| Lab 13 | Drift detection | Compliance reporting can be read-only and evidence-based. |

## Services Used Across the Labs

| Service or Tool | Introduced | Used For |
|---|---|---|
| GitLab.com | Lab 1 / Lab 2 | Git repositories, merge requests, pipeline coordination |
| GitLab Runner | Lab 1 | Local execution of GitLab.com jobs that need workstation services and DevNet VPN access |
| Cisco DevNet Catalyst C8KV IOS XE reservable sandbox | Lab 2 | Router target for CLI, RESTCONF, NETCONF, telemetry, and route-assistant labs |
| NetBox | Lab 1 / Lab 4 | Source of truth for managed loopback intent |
| HashiCorp Vault | Lab 1 / Lab 5 | Device credential storage and retrieval |
| Cisco YANG Suite | Lab 1 / Lab 6 / Lab 12 | Local `https://localhost:8443` or Cisco DevNet Sandbox `http://10.10.20.50:8480`; model discovery and payload testing |
| Local TIG stack | Lab 1 / Lab 10 | Application logs, automation metrics, and telemetry from a locally hosted C8KV |
| Cisco DevNet Sandbox TIG stack | Lab 12 | Integrated Telegraf at `10.10.20.50:57500` and Grafana at `http://10.10.20.50:3000` |
| Docker | Lab 1 / Lab 11 | Runtime packaging and local service hosting |
| LLM provider | Lab 14 | Local Ollama or learner-owned OpenAI/Anthropic API account |
| FastMCP | Lab 14 | Controlled AI tool boundary for network information |

All course containers use Linux host networking. NetBox, TIG, local YANG Suite, and Lab 11 runtime containers therefore inherit the workstation's Cisco DevNet VPN route, DNS, proxy, and cloud connectivity. Containers use `127.0.0.1` for local host-networked dependencies; Docker service names such as `influxdb` are not used. The GitLab shell Runner already executes in the host network namespace, and every `docker run` command in the course uses `--network host`.

## Shared Project File Convention

Labs 3–13 extend the files that already exist in `network_automation_project`. When a lab introduces another dependency, variable, or Ansible setting, learners modify the existing `requirements.txt`, `.env`, or `ansible.cfg` file rather than creating a lab-specific replacement.

When a later lab supplies a project file, open that file and the destination project in Visual Studio Code, then copy and paste the content into the location identified by the lab. This keeps the repository history understandable and makes each enhancement visible in Git. The `.env` file must remain excluded by `.gitignore` because it contains local endpoints and may contain credentials during the earlier project stages.

Start only the services required by the current lab:

| Service | Start and verify | Stop when unused |
|---|---|---|
| NetBox | `cd ~/lab-services/netbox-docker && docker compose up -d`, then open `http://127.0.0.1:8080` | `docker compose stop` |
| Local TIG | `cd ~/lab-services/tig && docker compose up -d`, then open Grafana at `http://127.0.0.1:3000` | `docker compose stop` |
| Local YANG Suite | `cd ~/lab-services/yangsuite/docker && docker compose up -d` | `docker compose stop` |
| Vault dev server | Start the Lab 5 `vault server -dev` command and run `vault status` | `Ctrl+C` in its dedicated terminal |
| GitLab Runner | `sudo systemctl start gitlab-runner && sudo gitlab-runner verify` | `sudo systemctl stop gitlab-runner` |
| Ollama | `ollama serve` and `ollama list` | `Ctrl+C` when run interactively |

## Where Learners Obtain Tokens

Use a separate, least-privilege token for each platform. Never reuse a token as a device password, paste it into source code, or include it in screenshots.

| Platform | How to create or obtain the token | Where the course uses it |
|---|---|---|
| NetBox | Sign in, select the user icon, open **API Tokens**, select **Add a Token**, disable write permission for read-only source-of-truth access, create it, and copy it once. | `NETBOX_TOKEN` in the existing project `.env` and as a masked GitLab CI/CD variable |
| Vault development server | Lab 5 starts Vault with `-dev-root-token-id="lab-root-token"`. Run `vault login token=lab-root-token`; the CLI stores it in `~/.vault-token`. | Interactive Python access and the protected `VAULT_TOKEN` GitLab variable |
| GitLab project runner | In the GitLab.com project, open **Settings > CI/CD > Runners > Create project runner**. Configure the protected runner and copy the temporary `glrt-...` authentication token into the registration command. | Registers the workstation Runner; it is not an application API token |
| GitLab pipeline trigger | Open **Settings > CI/CD > Pipeline trigger tokens**, create `netbox-loopback-trigger`, and copy the token once. | Embedded only in the private NetBox webhook URL |
| InfluxDB | Sign in to local InfluxDB, open **Load Data > API Tokens**, select **Generate Custom API Token**, grant write access only to the automation bucket, and copy it once. The initial local token may instead come from the Lab 1 `.env` initialization value. | Masked `INFLUX_TOKEN` GitLab variable for Lab 10 |
| Grafana | Browser dashboard work uses the learner login and needs no API token. If an instructor authorizes dashboard automation, open **Administration > Users and access > Service accounts**, create a narrowly scoped service account, add a token, and copy it once. | Optional Grafana API automation only; not required by the standard labs |
| OpenAI | In the OpenAI API platform project, open **API keys**, create a project key with the narrowest available permissions, and copy it once. | `OPENAI_API_KEY` in Lab 14's untracked `.env` |
| Anthropic | In the Anthropic Console workspace, open **API Keys**, create a lab-specific key, and copy it once. | `ANTHROPIC_API_KEY` in Lab 14's untracked `.env` |

Cisco DevNet Sandbox YANG Suite and Grafana use the credentials supplied with the reservation. They do not require learners to manufacture an additional API token for the standard course workflow.

## Working Practices for Every Lab

Use these habits consistently:

- Start from the correct repository and branch before copying lab files.
- Keep secrets out of Git. Modify the existing untracked `.env`; never commit it.
- Extend the existing `requirements.txt` and `ansible.cfg` rather than creating additional versions.
- Read the expected workflow before running commands.
- Confirm the sandbox reservation, required service, and configured endpoint before debugging application logic.
- Validate source-of-truth data before configuring devices.
- Inspect generated configuration or payloads before deployment when the lab supports it.
- Verify operational state after deployment.
- Preserve artifacts and logs because they are the evidence of what happened.
- When an API or model path fails, check product documentation and the deployed software version rather than assuming the sample is universal.

## Common Recovery Checklist

When a lab fails, work from the foundation upward:

1. Confirm the DevNet sandbox reservation is active and the VPN is connected.
2. Confirm required local services are running, such as NetBox, Vault, TIG, YANG Suite, or Ollama, or confirm that the selected Cisco DevNet Sandbox services are reachable.
3. Confirm the Python virtual environment is active.
4. Confirm required environment variables or GitLab CI/CD variables are present.
5. Confirm GitLab Runner is online when a pipeline is expected to run.
6. Confirm credentials are correct and not expired.
7. Confirm the IOS XE sandbox supports the requested RESTCONF, NETCONF, or telemetry model path.
8. Read the preserved logs or artifacts before rerunning the job.

## Completion Outcome

After Lab 14, learners should have practiced a complete professional network automation lifecycle. They will have developed an initial device-automation workflow into source-of-truth-driven change, secret management, model-driven configuration, CI/CD, observability, containerized execution, telemetry, compliance, and AI-assisted route analysis.

The final result is not one monolithic script. It is a set of engineering patterns that learners can reuse in real Cisco network automation work.
