locals {
  tenant_name = "ccnpauto-${var.learner_id}"
}

resource "aci_tenant" "course" {
  name        = local.tenant_name
  description = "Optional CCNPAUTO Terraform lab for ${var.learner_id}"
}

resource "aci_vrf" "production" {
  parent_dn   = aci_tenant.course.id
  name        = "PROD-VRF"
  description = "Production VRF managed by Terraform"
}

resource "aci_bridge_domain" "production" {
  parent_dn       = aci_tenant.course.id
  name            = "PROD-BD"
  description     = "Production bridge domain managed by Terraform"
  unicast_routing = "yes"

  relation_to_vrf = {
    vrf_name = aci_vrf.production.name
  }
}

resource "aci_subnet" "production" {
  parent_dn   = aci_bridge_domain.production.id
  ip          = var.subnet_gateway
  description = "Production anycast gateway"
  scope       = ["private"]
}

resource "aci_application_profile" "three_tier" {
  parent_dn   = aci_tenant.course.id
  name        = "THREE-TIER-APP"
  description = "Three-tier application profile managed by Terraform"
}

resource "aci_application_epg" "tier" {
  for_each = var.epgs

  parent_dn   = aci_application_profile.three_tier.id
  name        = each.value
  description = "${upper(each.key)} application tier"

  relation_to_bridge_domain = {
    bridge_domain_name = aci_bridge_domain.production.name
  }
}
