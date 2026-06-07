# Production Environment

Composes the four infrastructure modules into a complete AWS deployment.

## First-time setup

```bash
# 1. Install Terraform ≥ 1.5
brew install terraform   # macOS
# or see https://developer.hashicorp.com/terraform/install

# 2. Configure AWS credentials
aws configure   # enter Access Key ID + Secret for your admin user
# OR export AWS_PROFILE=your-profile

# 3. Copy and fill in secrets
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — see comments in the file

# 4. Initialise
terraform init

# 5. Review the plan (no changes applied yet)
terraform plan

# 6. Apply
terraform apply
```

After `terraform apply` completes, read the `next_steps` output:

```bash
terraform output next_steps
```

## Module dependency graph

```
iam ←─────────────────────────────────────────────┐
networking ←──────────────────────────────────────┤
cognito ←─────────────────────────────────────────┤
                                                   └── compute
```

Terraform handles the ordering automatically via `depends_on`.

## Migrating to a different AWS account

1. Create (or use) an IAM user in the new account with `AdministratorAccess`
2. Run `aws configure` with the new credentials
3. Update `terraform.tfvars`:
   - Change `aws_region` if needed
   - Change `cognito_domain_prefix` (must be globally unique)
   - Update `ssh_allowed_cidrs` to your new IP
   - Update `owner_email`
   - Everything else can stay the same
4. Run `terraform init && terraform apply`

No module code changes are needed — all account-specific values are in
`terraform.tfvars`.

## Cost estimate (free tier)

| Service | Free tier | After free tier |
|---|---|---|
| EC2 t2.micro | 750 h/month (12 months) | ~$8.50/month |
| Elastic IP | Free while attached | $0.005/h if unattached |
| Cognito | 50,000 MAU (no expiry) | $0.0055/MAU |
| Data transfer | 1 GB/month out | $0.09/GB |
| **Total (free tier)** | **~$0** | **~$10/month** |

## Destroying the environment

```bash
terraform destroy
```

This deletes all resources.  The PostgreSQL data on EC2 is lost — take a
backup first (`pg_dump -U mitumba_user mitumba_db > backup.sql`).
