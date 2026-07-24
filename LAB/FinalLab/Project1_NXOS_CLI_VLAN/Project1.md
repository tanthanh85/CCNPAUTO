# Project 1: CLI automation for legacy devices

## Business Scenario

Apex Global Services still operates a small legacy switching environment in one data center. The network team frequently receives requests to create VLANs for application teams, HR systems, IT infrastructure, and temporary migration projects. These switches are managed through SSH CLI in this project, so the company needs a safe and repeatable CLI automation workflow.

Most of the project has already been written. Your task is to complete the missing pieces so the automation can read VLAN intent from YAML, render NX-OS CLI configuration, connect to the Nexus sandbox switch with Netmiko, and create the VLANs.

## Points

Project 1 is worth **30 points**.

| Task | Requirement | Points |
|---|---|---:|
| 1 | Add switch login credentials to `.env` | 10 |
| 2 | Complete the Jinja2 VLAN configuration template | 10 |
| 3 | Complete the Netmiko `device` dictionary used by `ConnectHandler(**device)` | 10 |

## Project Files

```text
Project1_NXOS_CLI_VLAN/
├── .env.example
├── Project1.md
├── README.md
├── data/
│   └── vlans.yaml
├── requirements.txt
├── scripts/
│   ├── apply_vlans.py
│   └── grade_project1.py
├── src/
│   ├── device.py
│   ├── settings.py
│   └── vlan_source.py
└── templates/
    └── vlans.j2
```

## Task 1: Add NX-OS Login Credentials

Before editing project files, create a Python virtual environment and install the required libraries:

```bash
python3 -m venv final_lab
source final_lab/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create your local `.env` file:

```bash
cp .env.example .env
nano .env
```

Update the values from your Nexus NX-OS sandbox reservation:

```text
NXOS_HOST=<nxos-sandbox-host-or-ip>
NXOS_USERNAME=<sandbox-username>
NXOS_PASSWORD=<sandbox-password>
NXOS_PORT=22
```

Do not commit `.env` to Git.

## Task 2: Build the VLAN Jinja2 Template

The VLAN intent is already stored in [data/vlans.yaml](data/vlans.yaml). Your job is to complete [templates/vlans.j2](templates/vlans.j2).

The template must render this style of NX-OS configuration:

```text
vlan 10
  name IT
vlan 20
  name HR
```

The YAML file may contain more than two VLANs, so the loop must be implemented in the Jinja2 template, not in the Python script.

## Task 3: Complete the Netmiko Device Dictionary

Open [src/device.py](src/device.py) and complete the `device` dictionary.

Netmiko `ConnectHandler()` accepts connection parameters from a Python dictionary. The script already calls:

```python
ConnectHandler(**device)
```

Your job is to complete the dictionary that Netmiko needs. Use the correct Netmiko `device_type` value for Cisco Nexus NX-OS and include the host, username, password, and port from the `settings` object.

## Run the Automation

If you opened a new terminal, activate the virtual environment again:

```bash
source final_lab/bin/activate
```

Preview the rendered configuration:

```bash
python scripts/apply_vlans.py --dry-run
```

Apply the VLANs:

```bash
python scripts/apply_vlans.py
```

Verify on the Nexus switch:

```text
show vlan brief
```

## Self-Grading

Run:

```bash
python scripts/grade_project1.py
```

The grader checks the three required tasks and reports your score out of 30.
