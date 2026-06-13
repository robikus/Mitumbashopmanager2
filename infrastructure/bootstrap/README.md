# Bootstrap

Run this **once**, from **any laptop**, before deploying anything else.
Creates the S3 bucket and DynamoDB table that store Terraform state for all
other workspaces.

## Steps

```bash
cd infrastructure/bootstrap

# Make sure AWS credentials are configured
aws configure   # or: export AWS_PROFILE=your-profile

terraform init
terraform apply
```

After apply, copy the `next_step` output into
`infrastructure/environments/production/main.tf` and run `terraform init`
there to migrate state to S3.

## Why local state is fine here

This workspace manages only two resources (S3 bucket + DynamoDB table).
The state file contains no secrets — just names and ARNs. It is safe to
commit `bootstrap/terraform.tfstate` to a **private** repo, or simply keep
it on one machine (you'd only re-run this if you accidentally delete the
bucket, which is protected by `prevent_destroy = true`).

## Switching to a new AWS account

```bash
aws configure   # point at the new account
terraform apply # creates a new bucket + table in the new account
```

Copy the new bucket name into the production backend block and run
`terraform init` in `environments/production/`.
