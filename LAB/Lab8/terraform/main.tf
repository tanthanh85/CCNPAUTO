provider "vault" {}

data "vault_kv_secret_v2" "iosxe" {
  mount = "secret"
  name  = "ccnpauto/iosxe"
}

provider "iosxe" {
  host     = var.iosxe_host
  username = data.vault_kv_secret_v2.iosxe.data["username"]
  password = data.vault_kv_secret_v2.iosxe.data["password"]
  protocol = "restconf"
  insecure = true
}

locals {
  loopbacks = {
    "801" = "198.18.80.1"
    "802" = "198.18.80.2"
    "803" = "198.18.80.3"
  }
}

resource "iosxe_interface_loopback" "lab8" {
  for_each          = local.loopbacks
  name              = tonumber(each.key)
  description       = "LAB8_MANAGED_BY_TERRAFORM"
  shutdown          = false
  ipv4_address      = each.value
  ipv4_address_mask = "255.255.255.255"
  delete_mode       = "all"
}
