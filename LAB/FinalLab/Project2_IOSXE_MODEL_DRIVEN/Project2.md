# Project 2: Model-Driven Automation and Monitoring

## Business Scenario

Apex Global Services is modernizing its campus and WAN infrastructure. New IOS XE routers support NETCONF, RESTCONF, and YANG, so the network automation team wants to stop relying only on CLI screen scraping. The company has asked for a small model-driven automation project that can configure static routes from YAML, retrieve credentials from Vault, and expose a simple portal showing CPU, memory, and interface utilization.

Most of the project is already complete. Your job is to complete the missing model-driven parts.

## Points

Project 2 is worth **70 points**.

| Task | Requirement | Points |
|---|---|---:|
| 1 | Build the NETCONF XML payload template with a Jinja2 loop using Cisco IOS XE Native YANG | 20 |
| 2 | Complete the Vault credential retrieval function | 30 |
| 3 | Locate and place RESTCONF monitoring URIs for CPU, memory, and GigabitEthernet1 | 20 |

## Project Files

```text
Project2_IOSXE_MODEL_DRIVEN/
├── .env.example
├── Project2.md
├── README.md
├── app.py
├── data/
│   └── static_routes.yaml
├── requirements.txt
├── scripts/
│   ├── configure_static_routes.py
│   └── grade_project2.py
├── src/
│   ├── restconf_monitor.py
│   ├── route_source.py
│   ├── settings.py
│   └── vault_credentials.py
├── static/
│   └── portal.css
├── templates/
│   └── static_routes.xml.j2
└── templates_flask/
    └── portal.html
```

## Task 1: Build the NETCONF XML Payload Template

Before editing project files, create a Python virtual environment and install the required libraries:

```bash
python3 -m venv final_lab
source final_lab/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Static-route intent is already defined in [data/static_routes.yaml](data/static_routes.yaml). The starter template already contains the NETCONF `<config>` root element and the Jinja2 loop over `static_routes`. Your task is to use Cisco YANG Suite to construct the correct **Cisco IOS XE Native YANG** XML structure for one static route and place that structure inside the loop in [templates/static_routes.xml.j2](templates/static_routes.xml.j2).

In YANG Suite, choose the Cisco IOS XE native module, commonly shown as **`Cisco-IOS-XE-native`**. Do not build this task with the generic IETF routing model. This project is intentionally testing the Cisco native model because it closely matches the IOS XE CLI configuration hierarchy.

The YAML format is:

```yaml
static_routes:
  - prefix: 203.0.113.0
    mask: 255.255.255.0
    next_hop: 10.10.20.254
    description: Example business route
```

Use YANG Suite to inspect **`Cisco-IOS-XE-native`** for static routes under the IOS XE native configuration hierarchy. Then complete the XML payload body suitable for NETCONF `<edit-config>`. Do not hard-code only one route. The starter file already provides this Jinja2 loop:

```jinja2
{% for route in static_routes %}
  <!-- Add the Cisco native static-route XML for one route here -->
{% endfor %}
```

The XML you add inside that loop must use `route.prefix`, `route.mask`, and `route.next_hop`.

When the YAML file contains two or more routes, the rendered XML should contain two or more static-route entries. This is the main skill being tested in Task 1: discover the Cisco native YANG structure once, then use Jinja2 to repeat that structure for each desired static route.

After completing the template, first render it:

```bash
source final_lab/bin/activate
cp .env.example .env
nano .env
python scripts/configure_static_routes.py --dry-run
```

Then add a second route to [data/static_routes.yaml](data/static_routes.yaml) and run the dry run again. If the rendered XML now contains both static routes, configure the routes:

```bash
python scripts/configure_static_routes.py
```

Verify on the router:

```text
show ip route static
```

## Task 2: Move IOS XE Credentials to Vault

The project can initially read credentials from environment variables. Your task is to complete the Vault integration so the script can retrieve IOS XE credentials from Vault.

Start Vault if it is not running:

```bash
vault server -dev -dev-root-token-id=root
```

In another terminal:

```bash
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
vault kv put secret/ccnpauto/final/iosxe \
  username='<iosxe-username>' \
  password='<iosxe-password>'
```

Update `.env`:

```text
USE_VAULT=true
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=root
VAULT_SECRET_PATH=ccnpauto/final/iosxe
```

Open [src/vault_credentials.py](src/vault_credentials.py) and complete `get_iosxe_credentials_from_vault()`.

The function should:

- create an `hvac.Client`,
- authenticate with `VAULT_ADDR` and `VAULT_TOKEN`,
- read the KV version 2 secret from `VAULT_SECRET_PATH`,
- and return a dictionary with `username` and `password`.

After completing the function, add one more static route to [data/static_routes.yaml](data/static_routes.yaml), rerun the script, and verify the new route.

## Task 3: Complete RESTCONF Monitoring URIs

The project includes a small Flask management portal that refreshes every 5 seconds. Most of the code is complete, but the RESTCONF URIs are missing.

Use Cisco YANG Suite to locate RESTCONF operational paths for:

- CPU utilization,
- memory utilization,
- and GigabitEthernet1 interface counters or utilization.

Open [src/restconf_monitor.py](src/restconf_monitor.py) and complete:

```python
CPU_URI = ""
MEMORY_URI = ""
INTERFACE_GIG1_URI = ""
```

Place the RESTCONF data paths only. Do not include the scheme, hostname, or `/restconf/data` base in these constants. The code adds the base URL automatically.

Use this format:

```python
CPU_URI = "/Cisco-IOS-XE-process-cpu-oper:..."
```

Run the portal:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5060
```

The portal should show CPU, memory, and GigabitEthernet1 information and refresh automatically.

## Self-Grading

Run:

```bash
python scripts/grade_project2.py
```

The grader reports your score out of 70.

## Notes

If a RESTCONF or NETCONF path does not work on your IOS XE sandbox release, verify the model with YANG Suite. The model exposed by the device is authoritative.
