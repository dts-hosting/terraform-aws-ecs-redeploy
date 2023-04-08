variable "cluster" {}
variable "profile" {}
variable "token_key" {}

provider "aws" {
  region  = local.region
  profile = var.profile
}

locals {
  name   = "redeploy-ex-${basename(path.cwd)}"
  region = "us-west-2"

  tags = {
    Name       = local.name
    Example    = local.name
    Repository = "https://github.com/dts-hosting/terraform-ecs-redeploy"
  }
}

module "redeploy" {
  source = "../.."

  cluster   = var.cluster
  name      = local.name
  token_key = var.token_key
}

output "redeploy_url" {
  value = module.redeploy.redeploy_url
}
