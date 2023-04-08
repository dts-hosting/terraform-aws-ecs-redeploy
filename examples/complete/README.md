# Complete Redeploy example

Configuration in this directory creates a redeploy function url.

## Usage

To run this example you need to create `terraform.tfvars`:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Then execute:

```bash
terraform init
terraform plan
terraform apply
```

Note that this example creates resources which cost money. Run terraform destroy
when you don't need these resources.
