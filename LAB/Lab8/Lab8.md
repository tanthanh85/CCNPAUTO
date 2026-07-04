# Lab 8: Vault-Backed Automation with Ansible and Terraform

## Lab Introduction

This lab applies two declarative automation tools to one reservable IOS XE sandbox. Ansible merges three static routes through the CLI resource module, while Terraform manages three loopback interfaces through Cisco's IOS XE provider and RESTCONF. Neither project stores the device username or password. Both retrieve the same credential record from HashiCorp Vault, demonstrating how automation code can remain shareable while secrets stay outside Git.

## Learning Objectives

- Store and retrieve IOS XE credentials with Vault KV v2.
- Use an Ansible Vault lookup without placing device passwords in inventory.
- Configure three static Null0 routes idempotently.
- Use Terraform provider and resource lifecycles.
- Create three loopbacks with `for_each`.
- Interpret plan, apply, state, drift, and destroy behavior.
- Explain secret exposure risks in Terraform state.

## Prerequisites and Ownership

Use the Ubuntu 26.04 workstation and Vault installation from Lab 1 plus a reserved IOS XE sandbox. The lab owns:

- Static routes `198.51.100.0/24`, `203.0.113.0/24`, and `192.0.2.128/25`, all to Null0
- Loopback801–803 with `198.18.80.1/32` through `198.18.80.3/32`

Verify that these resources are unused before proceeding. Do not save the sandbox running configuration to startup configuration.

## Task 1: Create the Project

Create a blank GitLab project named `lab8-vault-automation`, clone it, and copy the Lab 8 files. Install the Vault Python client and Ansible collections:

```bash
source "$HOME/.venvs/ccnpauto/bin/activate"
python -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
ansible-galaxy collection list | grep -E 'cisco.ios|community.hashi_vault'
```

## Task 2: Start and Secure the Training Vault

Start the Lab 1 development Vault in a dedicated terminal if it is not running:

```bash
export VAULT_ADDR=http://127.0.0.1:8200
vault status
```

Set the Lab 1 development token without committing it:

```bash
export VAULT_TOKEN='REPLACE_WITH_LAB1_DEV_TOKEN'
vault token lookup
```

Write the sandbox credentials:

```bash
vault kv put secret/ccnpauto/iosxe \
  username='SANDBOX_USERNAME' \
  password='SANDBOX_PASSWORD'
vault kv get secret/ccnpauto/iosxe
```

Vault development mode is memory-backed, unsealed, and unsuitable for production. The exercise teaches the client workflow, not production Vault architecture.

## Task 3: Configure the Ansible Inventory

Edit `inventory/hosts.yml` with the reserved SSH host and port. Credentials must remain absent. Confirm the resolved inventory:

```bash
ansible-inventory -i inventory/hosts.yml --graph
```

The playbook uses the `community.hashi_vault` lookup to read `secret/data/ccnpauto/iosxe`. Only the Vault address and short-lived training token are present in the process environment.

## Task 4: Preview and Apply Three Static Routes

Run syntax and check modes:

```bash
ansible-playbook -i inventory/hosts.yml ansible/static_routes.yml --syntax-check
ansible-playbook -i inventory/hosts.yml ansible/static_routes.yml --check --diff
```

Apply the routes:

```bash
ansible-playbook -i inventory/hosts.yml ansible/static_routes.yml --diff
```

Null0 makes the routes deterministic without inventing a reachable next-hop router. Because the module uses `state: merged`, unrelated static routes remain untouched. Run the playbook again; the second result should report no change.

Verify independently:

```text
show running-config | include ^ip route
show ip route static
```

## Task 5: Initialize Terraform

Copy the variable example and enter the RESTCONF host:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform fmt -check
terraform init
terraform validate
```

The Vault provider reads `VAULT_ADDR` and `VAULT_TOKEN`. The IOS XE provider receives username and password from the Vault data source. Do not add literal credentials to `.tf` or `.tfvars` files.

## Task 6: Plan and Create Three Loopbacks

Review the plan carefully:

```bash
terraform plan -out lab8.tfplan
terraform show lab8.tfplan
terraform apply lab8.tfplan
terraform output
```

`for_each` gives each interface a stable key rather than relying on list order. Verify:

```text
show ip interface brief | include Loopback80
show running-config | section ^interface Loopback80
```

Run `terraform plan` again. A no-change plan demonstrates convergence between configuration, state, and observed device data.

## Task 7: Examine State and Secret Risk

List resources without printing the full state:

```bash
terraform state list
terraform state show 'iosxe_interface_loopback.lab8["801"]'
```

Terraform state is sensitive. Provider and data-source values may be retained depending on provider behavior. The local state is ignored by Git, but production workflows require encrypted remote state, restrictive access, locking, auditing, and secret-rotation procedures.

## Task 8: Observe Drift

With instructor approval, change the description of Loopback802 through CLI. Run:

```bash
terraform plan
```

Terraform should propose restoring the declared value. Apply only after reviewing the plan. This demonstrates remediation, but automated drift correction must never overwrite an authorized emergency change without coordination.

## Task 9: Clean Up

Remove Terraform-managed loopbacks first:

```bash
terraform plan -destroy
terraform destroy
```

Remove only the Ansible-owned routes:

```bash
cd ..
ansible-playbook -i inventory/hosts.yml ansible/remove_static_routes.yml --diff
```

Confirm the resources are absent, unset the token, and stop the development Vault when appropriate:

```bash
unset VAULT_TOKEN
```

## Key Takeaways

- Vault separates secret storage from automation source code.
- Ansible resource modules merge structured intent and expose idempotent results.
- Terraform plans make resource lifecycle changes reviewable before application.
- Terraform state requires protection equal to other sensitive automation data.
- Ansible is well suited to task-oriented configuration; Terraform is well suited to declared resource lifecycle.

The next lab packages a network application into a portable Docker image.

## References

- [Ansible IOS static routes](https://docs.ansible.com/projects/ansible/latest/collections/cisco/ios/ios_static_routes_module.html)
- [Cisco IOS XE Terraform provider](https://registry.terraform.io/providers/CiscoDevNet/iosxe/latest/docs)
- [Vault KV secrets engine](https://developer.hashicorp.com/vault/docs/secrets/kv)
