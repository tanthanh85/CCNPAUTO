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
| Project 1 | CLI automation for legacy devices | Cisco Nexus NX-OS sandbox switch | 30 |
| Project 2 | Model-driven automation and monitoring | Cisco IOS XE reservable sandbox router | 70 |
| **Total** |  |  | **100** |

## Required Lab Access

You need access to:

- Cisco Nexus NX-OS sandbox switch
- Cisco IOS XE reservable sandbox router
- Cisco YANG Suite from Lab 1
- HashiCorp Vault from Lab 1
- Python virtual environment from earlier labs

## Suggested Working Directory

Copy the final lab projects into your workspace:

```bash
mkdir -p ~/ccnpauto-workspace/final_assessment
cp -R /Users/thandoan/Documents/Presentations/CCNPAUTO/LAB/FinalLab/Project1_NXOS_CLI_VLAN \
  ~/ccnpauto-workspace/final_assessment/
cp -R /Users/thandoan/Documents/Presentations/CCNPAUTO/LAB/FinalLab/Project2_IOSXE_MODEL_DRIVEN \
  ~/ccnpauto-workspace/final_assessment/
cd ~/ccnpauto-workspace/final_assessment
```

Create one GitLab.com repository named `ccnpauto_final_assessment` if your instructor asks you to submit through Git. Otherwise, you can work locally and submit the completed folder.

## Python Environment and Required Libraries

Each project includes its own `requirements.txt` file. Install the required libraries before running the project scripts or self-graders. You may use one shared virtual environment for the final assessment, or you may create a separate virtual environment inside each project folder.

Recommended shared environment:

```bash
cd ~/ccnpauto-workspace/final_assessment
python3 -m venv final_lab
source final_lab/bin/activate
python -m pip install --upgrade pip
python -m pip install -r Project1_NXOS_CLI_VLAN/requirements.txt
python -m pip install -r Project2_IOSXE_MODEL_DRIVEN/requirements.txt
```

Keep the virtual environment active while working on both projects:

```bash
source ~/ccnpauto-workspace/final_assessment/final_lab/bin/activate
```

## Project 1 Overview: CLI automation for legacy devices

Project 1 represents a legacy data-center automation task. The Nexus switch does not use NETCONF or RESTCONF in this project. Your automation must use SSH CLI through Netmiko and create VLANs from YAML intent.

You need to complete three tasks:

1. Add the Nexus switch login credentials to `.env`.
2. Construct the Jinja2 template that renders VLAN configuration from YAML.
3. Complete the Netmiko `device` dictionary used by `ConnectHandler(**device)`.

Run the self-grader from the project folder:

```bash
cd ~/ccnpauto-workspace/final_assessment/Project1_NXOS_CLI_VLAN
python -m pip install -r requirements.txt
python scripts/grade_project1.py
```

Project 1 is worth **30 points**.

## Project 2 Overview: Model-Driven Automation and Monitoring

Project 2 represents a newer programmable network platform. The IOS XE router supports NETCONF and RESTCONF. The project includes static-route automation, Vault credential retrieval, and a small management portal that monitors CPU, memory, and GigabitEthernet1 utilization.

You need to complete three tasks:

1. Use Cisco YANG Suite to construct the XML structure for static routes with Cisco IOS XE Native YANG, then convert it into a Jinja2 template with a loop over the YAML route list.
2. Complete the Vault credential retrieval function.
3. Use Cisco YANG Suite to locate the RESTCONF URIs for CPU, memory, and GigabitEthernet1 monitoring, then place those URIs into the code.

Run the self-grader from the project folder:

```bash
cd ~/ccnpauto-workspace/final_assessment/Project2_IOSXE_MODEL_DRIVEN
python -m pip install -r requirements.txt
python scripts/grade_project2.py
```

Project 2 is worth **70 points**.

## Submission Evidence

Your instructor may ask for:

- completed project files,
- self-grader output,
- screenshots showing successful VLAN/static-route deployment,
- screenshot of the monitoring portal,
- and Git commit history.

Do not submit real passwords, Vault tokens, or private keys.

## Final Reminder

The assessment is designed to test practical judgment, not memorization. Use the tools you practiced earlier: `.env` files for local variables, Vault for secrets, Jinja2 for rendering, YAML for intent, YANG Suite for model discovery, Netmiko for CLI devices, NETCONF for model-driven configuration, RESTCONF for operational data, and Flask for a simple operational portal.
