output "managed_loopbacks" {
  value = {
    for id, resource in iosxe_interface_loopback.lab8 :
    id => resource.ipv4_address
  }
}
