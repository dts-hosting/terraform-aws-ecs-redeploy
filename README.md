# Terraform AWS ECS redeploy

Terraform module to create an AWS Lambda Function URL that redeploys ECS services.

## Examples

- [Create redeploy function url](examples/complete)

## Usage

```hcl
module "redeploy" {
  source = "github.com/dts-hosting/terraform-aws-ecs-redeploy//modules/redeploy"

  cluster          = var.cluster # ECS cluster name
  name             = var.name # Name applied to AWS resources that are created
  notification_key = var.n_key # (optional) SSM param name for notification webhook
  token_key        = var.token_key # SSM param name for token (basic authz)
  timezone         = var.timezone # Timezone for notification date (default UTC)
}
```

The `token_key` SSM parameter is NOT created by this module. It must be
created separately and is never captured in Terraform state.

The `notification_key` value should be a URL that can receive a basic redeploy
confirmation message (POST data), such as a Slack webhook url.

### Invoking the function

The simplest URL requires:

- lambda url (available via terraform outputs)
- query params:
  - cluster (name)
  - service (name)
  - token (value)

```bash
curl -v -X POST \
  'https://$id.lambda-url.$region.on.aws/?cluster=$cluster&service=$service&token=$token'
```

Assuming a redeploy function was deployed with a matching `cluster` name, for a cluster
that has a service identified by `service`, and the `token` matches the token SSM param
value the function accesses then the service will be redeployed.

For more control a `tag` parameter can be included in the url. When this is present the
redeploy will only occur if the POST body includes `push_data.tag` with a matching value:

```bash
curl -v -X POST \
  -H "content-type: application/json" \
  -d '{ "push_data": { "tag": "latest" } }' \
  'https://$id.lambda-url.$region.on.aws/?cluster=$cluster&service=$service&token=$token&tag=latest'
```

This is useful when webhook services are triggered in automated environments and you need
to ensure that a service is only restarted when a matching tag is pushed (not when any tag
is pushed).

## Local debug

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
