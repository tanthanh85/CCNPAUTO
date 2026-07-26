# Final Assessment Lab: Enterprise Network Automation Delivery

## Scenario

You are part of the network automation team for **Apex Global Services**, a company that operates both legacy data-center networks and newer programmable campus infrastructure. The business has asked your team to reduce manual configuration work, improve change consistency, and provide simple operational visibility for support engineers.

The environment is mixed. Some older devices do not expose modern model-driven interfaces, so the team still needs CLI-based automation. Newer IOS XE devices support NETCONF, RESTCONF, and YANG, so the team wants model-driven automation for those platforms. The company also recently adopted a basic secrets-management policy, which means device credentials should not remain hard-coded or scattered across local files.

You have inherited two mostly completed automation projects. Your job is to complete the missing parts, run the projects, and use the self-grading scripts to confirm your result.

## Time Allowed

You have **4 hours** to complete the final lab.

## Assessment Structure

| Project | Topic | Platform | Max Points |
|---|---|---|---:|
| Project 1 | CLI automation for legacy devices | Cisco Nexus NX-OS sandbox switch | 50 |
| Project 2 | Model-driven automation and monitoring | Cisco IOS XE reservable sandbox router | 50 |
| **Total** |  |  | **100** |

## Required Lab Access

You need access to:

- Cisco Nexus NX-OS sandbox switch
- Cisco IOS XE reservable sandbox router
- Access to local Cisco Yangsuite at `https://localhost:8443` or Cisco DevNet Sandbox Yangsuite at `http://10.10.20.50:8480`
- HashiCorp Vault from Lab 1

The assessment does not use NetBox, TIG, or GitLab Runner. Stop them to preserve workstation resources, then verify Vault and the selected Yangsuite option:

```bash
test -d "$HOME/lab-services/netbox-docker" && \
  (cd "$HOME/lab-services/netbox-docker" && docker compose stop)
test -d "$HOME/lab-services/tig" && \
  (cd "$HOME/lab-services/tig" && docker compose stop)
sudo systemctl stop gitlab-runner
vault status
```

If `vault status` fails, start the development server in a dedicated terminal and recreate the assessment secret. For local Yangsuite, start it from `~/lab-services/yangsuite/docker`; otherwise open Cisco DevNet Sandbox Yangsuite at `http://10.10.20.50:8480`.

## Suggested Working Directory

Create `~/ccnpauto-workspace/final_assessment`. Using the VS Code Explorer, copy and paste the complete `Project1_NXOS_CLI_VLAN` and `Project2_IOSXE_MODEL_DRIVEN` folders from `CCNPAUTO/LAB/FinalLab/` into that working directory.

```bash
mkdir -p ~/ccnpauto-workspace/final_assessment
cd ~/ccnpauto-workspace/final_assessment
```

Create one GitLab.com repository named `ccnpauto_final_assessment` if your instructor asks you to submit through Git. Otherwise, you can work locally and submit the completed folder.

## Python Environment and Required Libraries

Each project includes its own `requirements.txt` file. Use a separate virtual
environment inside each project folder so one project's dependencies do not
hide a dependency fault in the other project. Name the Project 1 environment
`final_lab1` and the Project 2 environment `final_lab2`.

Prepare Project 1 first:

```bash
cd ~/ccnpauto-workspace/final_assessment/Project1_NXOS_CLI_VLAN
python3 -m venv final_lab1
source final_lab1/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

After finishing Project 1, deactivate its environment and prepare Project 2:

```bash
deactivate
cd ~/ccnpauto-workspace/final_assessment/Project2_IOSXE_MODEL_DRIVEN
python3 -m venv final_lab2
source final_lab2/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Project 1 deliberately omits a runtime-configuration example. Learners must
trace the Python imports and settings code to determine the configuration
mechanism, local filename, and variable names expected by the NX-OS
application. Project 2 supplies `.env.example` because its assessment focus is
Vault, NETCONF, RESTCONF, and monitoring rather than environment discovery.
Never commit a local secret file or place real credentials in an example
file.

## Project 1 Overview: CLI automation for legacy devices

Project 1 represents a legacy data-center automation task. The Nexus switch does not use NETCONF or RESTCONF in this project. Your automation must use SSH CLI through Netmiko and create VLANs from YAML intent.

You need to complete five tasks:

1. Diagnose the missing template-rendering Python dependency and install the
   package that supplies the imported module.
2. Trace the Python settings flow, identify the missing runtime configuration,
   and supply the Nexus reservation values without hard-coding secrets.
3. Construct the Jinja2 template that renders VLAN configuration from YAML.
4. Troubleshoot the incomplete Netmiko `device` dictionary and select the
   correct Nexus NX-OS platform identifier for `ConnectHandler(**device)`.
5. Handle `NetmikoAuthenticationException` and `NetmikoTimeoutException` with clear, failure-specific messages.

Each Project 1 task is worth 10 points, for a total of 50.

Run the self-grader from the project folder:

```bash
cd ~/ccnpauto-workspace/final_assessment/Project1_NXOS_CLI_VLAN
python -m pip install -r requirements.txt
python scripts/grade_project1.py
```

Project 1 is worth **50 points**.

## Project 2 Overview: Model-Driven Automation and Monitoring

Project 2 represents a newer programmable network platform. The IOS XE router supports NETCONF and RESTCONF. The project includes static-route automation, Vault credential retrieval, and a small management portal that monitors CPU, memory, and GigabitEthernet1 utilization.

You need to complete three tasks:

1. Use local Cisco Yangsuite or Cisco DevNet Sandbox Yangsuite at `http://10.10.20.50:8480` to construct the XML structure for static routes with Cisco IOS XE Native YANG, then convert it into a Jinja2 template with a loop over the YAML route list.
2. Complete the Vault credential retrieval function.
3. Use local or Cisco DevNet Sandbox Yangsuite to locate the RESTCONF URIs for CPU, memory, and GigabitEthernet1 monitoring, then place those URIs into the code.

Run the self-grader from the project folder:

```bash
cd ~/ccnpauto-workspace/final_assessment/Project2_IOSXE_MODEL_DRIVEN
python -m pip install -r requirements.txt
python scripts/grade_project2.py
```

Project 2 is worth **50 points**.

## Submission Evidence

Your instructor may ask for:

- completed project files,
- self-grader output,
- screenshots showing successful VLAN/static-route deployment,
- screenshot of the monitoring portal,
- and Git commit history.

Do not submit real passwords, Vault tokens, or private keys.

## Final Reminder

The assessment is designed to test practical judgment, not memorization. Use
the tools you practised earlier: environment-based runtime configuration,
Vault for secrets, Jinja2 for rendering, YAML for intent, local or Cisco
DevNet Sandbox Yangsuite for model discovery, Netmiko for CLI devices,
NETCONF for model-driven configuration, RESTCONF for operational data, and
Flask for a simple operational portal.
