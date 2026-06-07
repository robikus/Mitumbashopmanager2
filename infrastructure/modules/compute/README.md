# Module: compute

Launches a single Ubuntu 22.04 EC2 instance that runs the full stack:
Nginx + Gunicorn (Django) + PostgreSQL.

## Why single instance?

AWS free tier gives 750 h/month on t2.micro. Splitting into separate RDS and
EC2 instances would incur RDS charges (no free tier after 12 months). A
single instance is enough for a single-shop ERP with < 100 concurrent users.

## What the bootstrap script does (`user_data.sh`)

1. `apt-get` upgrades + installs Python 3.11, PostgreSQL 14, Nginx, Certbot
2. Creates the PostgreSQL database and role
3. Creates a Python virtualenv at `/opt/mitumba/venv` and installs all
   Python dependencies
4. Writes `/opt/mitumba/.env` with credentials passed via Terraform variables
5. Creates a systemd service `mitumba.service` (Gunicorn on Unix socket)
6. Configures Nginx as a reverse proxy
7. Enables both services on boot

After the instance is running you still need to:

```bash
# SSH into the instance
ssh -i ~/.ssh/your-key ubuntu@<elastic-ip>

# Deploy app code
sudo git clone https://github.com/your-org/mitumba.git /opt/mitumba/backend

# Run Django migrations
cd /opt/mitumba/backend
sudo -u www-data ../venv/bin/python manage.py migrate
sudo -u www-data ../venv/bin/python manage.py collectstatic --no-input

# Start the app server
sudo systemctl start mitumba

# Obtain TLS certificate (requires DNS pointing to the Elastic IP first)
sudo certbot --nginx -d your-domain.com
```

## Inputs

| Name | Description | Default |
|---|---|---|
| `project_name` | Resource name prefix | — |
| `aws_region` | AWS region | — |
| `instance_type` | EC2 type | `t2.micro` |
| `subnet_id` | Public subnet ID | — |
| `security_group_id` | SG ID from networking module | — |
| `ssh_public_key` | SSH public key content | — |
| `iam_instance_profile_name` | IAM profile for the instance | — |
| `db_name` | PostgreSQL DB name | `mitumba_db` |
| `db_user` | PostgreSQL user | `mitumba_user` |
| `db_password` | PostgreSQL password (sensitive) | — |
| `app_domain` | FQDN for the app | — |
| `django_secret_key` | Django SECRET_KEY (sensitive) | — |
| `cognito_*` | Cognito settings passed to .env | — |

## Outputs

| Name | Description |
|---|---|
| `instance_id` | EC2 instance ID |
| `public_ip` | Elastic IP — point your DNS A record here |
| `public_dns` | EIP public DNS name |
| `ami_id` | Ubuntu AMI used |

## Migrating to a different AWS account

Change `aws_region`, `subnet_id`, `security_group_id`, and `ssh_public_key`
in `terraform.tfvars`. The Ubuntu AMI is resolved dynamically via a data
source so it will automatically pick the correct AMI in the new region.
