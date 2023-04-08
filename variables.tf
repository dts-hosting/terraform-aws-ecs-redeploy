variable "cluster" {
  description = "ECS cluster name"
}

variable "name" {
  description = "Name for project / function resources"
}

variable "notification_key" {
  default     = ""
  description = "SSM param name for notification webhook url"
}

variable "timezone" {
  default     = "UTC"
  description = "Timezone for notification date"
}

variable "token_key" {
  description = "SSM param name for token (used for basic authz)"
}
