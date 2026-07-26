# Project 2: Model-Driven Automation and Monitoring

## Business Scenario

Apex Global Services is modernizing its campus and WAN infrastructure. New IOS XE routers support NETCONF, RESTCONF, and YANG, so the network automation team wants to stop relying only on CLI screen scraping. The company has asked for a small model-driven automation project that can configure static routes from YAML, retrieve credentials from Vault, and expose a simple portal showing CPU, memory, and interface utilization.

Most of the project is already complete. Your job is to complete the missing model-driven parts.

## Points

Project 2 is worth **50 points**.

| Task | Requirement | Points |
|---|---|---:|
| 1 | Build the NETCONF XML payload template with a Jinja2 loop using Cisco IOS XE Native YANG | 15 |
| 2 | Complete the Vault credential retrieval function | 20 |
| 3 | Locate and place RESTCONF monitoring URIs for CPU, memory, and GigabitEthernet1 | 15 |

## Project Files

```text
Project2_IOSXE_MODEL_DRIVEN/
├── .env.example
├── .env                 # Learner-created and not committed
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
python3 -m venv final_lab2
source final_lab2/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Static-route intent is already defined in [data/static_routes.yaml](data/static_routes.yaml). The starter template already contains the NETCONF `<config>` root element and the Jinja2 loop over `static_routes`. Open local Cisco Yangsuite at `https://localhost:8443` or Cisco DevNet Sandbox Yangsuite at `http://10.10.20.50:8480`. Your task is to use it to construct the correct **Cisco IOS XE Native YANG** XML structure for one static route and place that structure inside the loop in [templates/static_routes.xml.j2](templates/static_routes.xml.j2).

In Yangsuite, choose the Cisco IOS XE native module, commonly shown as **`Cisco-IOS-XE-native`**. Do not build this task with the generic IETF routing model. This project is intentionally testing the Cisco native model because it closely matches the IOS XE CLI configuration hierarchy.

Use this workflow:

1. In **Setup > Device profiles**, create or refresh the IOS XE reservation profile with NETCONF port `830`.
2. In **Setup > YANG files and repositories**, retrieve the schema list from that device and download `Cisco-IOS-XE-native` with its dependencies.
3. Add those files to a YANG module set.
4. In **Protocols > NETCONF**, select the device and module set, load `Cisco-IOS-XE-native`, and first build a `get-config` for the native routing subtree.
5. Run the read RPC and use the reply to confirm the hierarchy and namespaces accepted by the active IOS XE release.
6. Change the operation to `edit-config`, select the `running` target and `merge`, enter one temporary set of route values in the tree, and select **Build RPC**.
7. Copy only the generated `<config>...</config>` body into the template design because `ncclient.edit_config()` creates the outer `<rpc>` and `<edit-config>` elements.
8. Replace the temporary values with the supplied Jinja2 variables inside the existing loop.

The YAML format is:

```yaml
static_routes:
  - prefix: 203.0.113.0
    mask: 255.255.255.0
    next_hop: 10.10.20.254
    description: Example business route
```

Use Yangsuite to inspect **`Cisco-IOS-XE-native`** for static routes under the IOS XE native configuration hierarchy. Then complete the XML payload body suitable for NETCONF `<edit-config>`. Do not hard-code only one route. The starter file already provides this Jinja2 loop:

```jinja2
{% for route in static_routes %}
  <!-- Add the Cisco native static-route XML for one route here -->
{% endfor %}
```

The XML you add inside that loop must use `route.prefix`, `route.mask`, and `route.next_hop`.

When the YAML file contains two or more routes, the rendered XML should contain two or more static-route entries. This is the main skill being tested in Task 1: discover the Cisco native YANG structure once, then use Jinja2 to repeat that structure for each desired static route.

After completing the template, first create `.env` if it does not exist. Open `.env.example` in VS Code, create `.env` in the project root, and copy and paste the example content into it. Enter the active reservation values, then render the template:

```bash
source final_lab2/bin/activate
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

Use local Cisco Yangsuite or Cisco DevNet Sandbox Yangsuite at `http://10.10.20.50:8480` to locate RESTCONF operational paths for:

- CPU utilization,
- memory utilization,
- and GigabitEthernet1 interface counters or utilization.

For each metric:

1. Use the device profile and the YANG set downloaded from the active IOS XE reservation.
2. Select **Protocols > RESTCONF**, load the operational module, and use **Search module** to locate the required container or leaf.
3. Select that node and choose **Generate APIs**.
4. Use the generated API information to identify the `GET` resource path.
   Copy the device resource path that follows `/restconf/data/`; do not copy a
   Yangsuite proxy hostname or proxy prefix. Validate the request directly
   against IOS XE with Postman.
5. Open Postman and create a new **HTTP Request**. Set the method to `GET` and
   enter the direct IOS XE URL:

   ```text
   https://<IOSXE_HOST>:<IOSXE_RESTCONF_PORT>/restconf/data/<generated-resource-path>
   ```

6. On the **Authorization** tab, select **Basic Auth** and enter the active IOS
   XE reservation username and password.
7. On the **Headers** tab, add:

   ```text
   Accept: application/yang-data+json
   ```

8. The sandbox normally uses a self-signed HTTPS certificate. For this
   controlled assessment only, open **Postman Settings > General** and disable
   **SSL certificate verification** if certificate validation prevents the
   request.
9. Select **Send** and confirm that IOS XE returns `200 OK`. Inspect the JSON
   response and verify that it includes the field consumed by the portal.
10. When selecting one interface list entry, allow Yangsuite to generate the
    encoded list-key syntax for `GigabitEthernet1`; do not paste an XPath
    predicate into a RESTCONF URI.
11. Repeat the Postman request for CPU, memory, and interface data before
    placing any resource path into Python.

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

The grader reports your score out of 50. For every incomplete task, it
identifies the missing points and states what is required for full credit.
Correct the reported requirement and rerun the grader. The local checks
validate structure and completion; they do not replace NETCONF deployment,
Vault retrieval, RESTCONF `200 OK`, or portal verification against the
reserved router.

## Notes

If a RESTCONF or NETCONF path does not work on your IOS XE sandbox release, verify the model with local or Cisco DevNet Sandbox Yangsuite. The model exposed by the device is authoritative.
