# Infrastructure — Mitumba Shop Manager

Terraform code for deploying Mitumba Shop Manager on AWS.

## Architecture

```
Internet
    │
    ▼
Elastic IP (static)
    │
    ▼
EC2 t2.micro  (Ubuntu 22.04)
├── Nginx  (reverse proxy, static files, TLS termination via Certbot)
├── Gunicorn  (Django WSGI server, Unix socket)
└── PostgreSQL 14  (local, no RDS = free tier forever)

AWS Cognito  (hosted login UI, JWT tokens)
AWS IAM      (EC2 instance role, admin user)
AWS VPC      (isolated network, public subnet, security groups)
```

**Free tier cost: ~$0/month** (for 12 months, then ~$10/month for EC2)

## Directory structure

```
infrastructure/
├── modules/
│   ├── networking/   # VPC, subnet, IGW, security group
│   ├── compute/      # EC2, EIP, SSH key, bootstrap script
│   ├── cognito/      # User pool, hosted UI, app client
│   └── iam/          # EC2 instance role, admin IAM user
└── environments/
    └── production/   # Composes all modules; tfvars live here
```

Each module has its own `README.md` with inputs, outputs, and usage examples.

## Quick start

```bash
cd infrastructure/environments/production
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init && terraform apply
```

See [environments/production/README.md](environments/production/README.md) for
the full deployment guide.

## Design principles

- **Account-agnostic**: All account-specific values are variables, not hardcoded
- **Module isolation**: Each module can be used independently
- **Free tier first**: Defaults optimised for zero-cost (t2.micro, no RDS, no NAT)
- **Least privilege**: EC2 role has only the permissions it needs
- **No secrets in code**: All secrets are in `terraform.tfvars` (gitignored)
