output "tenant_dn" {
  description = "ACI distinguished name of the learner tenant."
  value       = aci_tenant.course.id
}

output "bridge_domain_dn" {
  description = "ACI distinguished name of the production bridge domain."
  value       = aci_bridge_domain.production.id
}

output "subnet" {
  description = "Configured ACI subnet gateway."
  value       = aci_subnet.production.ip
}

output "application_profile_dn" {
  description = "ACI distinguished name of the application profile."
  value       = aci_application_profile.three_tier.id
}

output "epg_dns" {
  description = "ACI distinguished names keyed by application tier."
  value       = { for key, epg in aci_application_epg.tier : key => epg.id }
}
