variable "learner_id" {
  description = "Short identifier used to keep sandbox objects unique."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.learner_id))
    error_message = "Use 3-20 lowercase letters, numbers, or hyphens."
  }
}

variable "subnet_gateway" {
  description = "Anycast gateway configured under the bridge domain."
  type        = string
  default     = "10.50.0.1/24"
}

variable "epgs" {
  description = "Application tiers created below the application profile."
  type        = map(string)
  default = {
    web = "WEB-EPG"
    app = "APP-EPG"
    db  = "DB-EPG"
  }
}
