# Project 1: CLI automation for legacy devices

## Business Scenario

Apex Global Services still operates a small legacy switching environment in one data center. The network team frequently receives requests to create VLANs for application teams, HR systems, IT infrastructure, and temporary migration projects. These switches are managed through SSH CLI in this project, so the company needs a safe and repeatable CLI automation workflow.

Most of the project has already been written. Your task is to complete the missing pieces so the automation can read VLAN intent from YAML, render NX-OS CLI configuration, connect to the Nexus sandbox switch with Netmiko, create the VLANs, and fail clearly when authentication or connection establishment does not succeed.

## Points

Project 1 is worth **50 points**.

| Task | Requirement | Points |
|---|---|---:|
| 1 | Diagnose and install the missing Python dependency | 10 |
| 2 | Diagnose and supply the missing runtime connection settings | 10 |
| 3 | Complete the Jinja2 VLAN configuration template | 10 |
| 4 | Troubleshoot and correct the Netmiko `device` dictionary | 10 |
| 5 | Handle Netmiko authentication and connection timeout failures | 10 |

## Project Files

```text
Project1_NXOS_CLI_VLAN/
├── Project1.md
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

## Task 1: Diagnose the Missing Python Dependency

Before editing project files, create a Python virtual environment and install the required libraries:

```bash
python3 -m venv final_lab1
source final_lab1/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the application in dry-run mode before changing the starter code:

```bash
python scripts/apply_vlans.py --dry-run
```

The application will stop during module import because the library used to
load and render the VLAN template is deliberately absent from
`requirements.txt`. Read the complete traceback, identify the missing import,
inspect `scripts/apply_vlans.py`, and determine which Python package supplies
that module. Install the missing package into the active `final_lab1`
environment with `python -m pip`.

Confirm that Python can import the module, then run the dry run again. Do not
install unrelated packages until the error disappears. This task assesses
whether you can distinguish a missing Python distribution from an application
logic failure.

## Task 2: Diagnose the Missing Runtime Configuration

The starter project deliberately does not include a runtime environment file
or an example containing the required variable names. Begin at
`scripts/apply_vlans.py` and follow its imports through `src/device.py` into
`src/settings.py`.

From the Python code, determine:

- how the application loads local environment values;
- which local file must be created in the project root;
- the exact variable names expected by the settings class;
- which values must come from the active Nexus NX-OS sandbox reservation;
- the data type and default used for the SSH port.

Create the required local file and enter the active reservation values. Do not
change `src/settings.py` merely to hard-code the credentials, and do not
commit the local secret file to Git. This task assesses whether you can trace
configuration dependencies in an unfamiliar Python application rather than
copy variable names from an example.

## Task 3: Build the VLAN Jinja2 Template

The VLAN intent is already stored in [data/vlans.yaml](data/vlans.yaml). Your job is to complete [templates/vlans.j2](templates/vlans.j2).

The template must render this style of NX-OS configuration:

```text
vlan 10
  name IT
vlan 20
  name HR
```

The YAML file may contain more than two VLANs, so the loop must be implemented in the Jinja2 template, not in the Python script.

## Task 4: Troubleshoot the Netmiko Device Dictionary

Open [src/device.py](src/device.py) and complete the `device` dictionary.

Netmiko `ConnectHandler()` accepts connection parameters from a Python dictionary. The script already calls:

```python
ConnectHandler(**device)
```

The host, username, password, and port are already mapped from the `settings`
object, but the starter dictionary is incomplete. Run the application after
completing Tasks 1–3, read the resulting Netmiko error, and compare the
dictionary with the arguments required by `ConnectHandler`.

Identify the missing key and determine the correct Netmiko platform identifier
for a Cisco Nexus switch running NX-OS. Use Netmiko's supported-platform
documentation if necessary, then correct the dictionary without replacing the
existing settings mappings with hard-coded values. The finished script must
continue to call:

```python
ConnectHandler(**device)
```

## Task 5: Handle Netmiko Connection Failures

Open [scripts/apply_vlans.py](scripts/apply_vlans.py). At present, an authentication failure or an unreachable SSH service produces an unhandled traceback. Wrap the `ConnectHandler(**device)` operation and its session body with specific exception handling for:

- `NetmikoAuthenticationException`
- `NetmikoTimeoutException`

Import both exception classes from `netmiko.exceptions`. The program must behave as follows:

| Failure | Required message |
|---|---|
| `NetmikoAuthenticationException` | A clear message containing the word `authentication` |
| `NetmikoTimeoutException` | A clear message containing `timeout` or `timed out` |

The exception handlers only need to display clear messages; they do not need to return special exit codes. Do not use a broad `except Exception` in place of the two specific Netmiko handlers. A timeout suggests that the host, port, VPN, routing, firewall, or SSH service is unreachable; it does not prove that the password is wrong. Conversely, an authentication exception proves that a session reached the SSH service but the presented identity was rejected.

## Run the Automation

If you opened a new terminal, activate the virtual environment again:

```bash
source final_lab1/bin/activate
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

The grader checks all five required tasks and reports a score out of 50. It
simulates both Netmiko exceptions locally and does not connect to the sandbox
while grading. For every incomplete task, it identifies the missing points
and states what is required for full credit. Correct the reported requirement
and rerun the grader. A full local score does not replace the final VLAN
deployment and `show vlan brief` verification on the sandbox.
