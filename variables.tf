variable "cluster" {
  description = "ECS cluster name"
}

variable "name" {
  description = "Name for project / function resources"
}

variable "slack_key" {
  default     = ""
  description = "SSM param name for Slack webhook url"
}

variable "token_key" {
  description = "SSM param name for token (used for basic authz)"
}
