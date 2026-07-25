terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aci = {
      source  = "ciscodevnet/aci"
      version = "~> 2.20"
    }
  }
}

provider "aci" {
  # Authentication and URL are read from ACI_* environment variables.
}
