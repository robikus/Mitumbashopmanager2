# Mitumba Shop Manager

A web-based ERP system for a small retail shop. Built on Django, PostgreSQL,
and AWS — designed to run entirely on the AWS free tier.

---

## Table of contents

1. [Application summary](#1-application-summary)
2. [Architecture](#2-architecture)
   - [Request flow](#request-flow)
   - [Authentication flow](#authentication-flow)
   - [User registration flow](#user-registration-flow)
3. [Infrastructure — Terraform](#3-infrastructure--terraform)
4. [Backend — Django](#4-backend--django)
5. [Administration](#5-administration)
   - [Approving new users](#approving-new-users-admin-panel)

---

## 1. Application summary

Mitumba Shop Manager is a single-page ERP web application for managing a
small second-hand (mitumba) clothing shop. It replaces a static HTML
prototype with a fully dynamic system backed by a database.

**Modules:**

| Module | What it does |
|---|---|
| Dashboard | Overview of current month — revenue, profit, stock value |
| Purchases | Record stock acquisitions (single pieces or bales) |
| Sales | Record individual sales with line items |
| Finance | Monthly profit & loss breakdown |
| Stock | Current stock levels per category |
| Settings | Per-user shop configuration (shop name, unsellable rate, categories) |

**Authentication and user onboarding:**

1. A new user fills in the public registration form at `/auth/register/`
   (name, email, phone number). Their request is stored in the database with
   status *pending* — no Cognito account is created yet.
2. The admin reviews pending requests at `/auth/admin/pending/` and confirms
   payment. Clicking **Approve** creates the Cognito account and emails the
   user a temporary password automatically.
3. The user logs in via the Cognito hosted UI, resets their password on first
   sign-in, and lands in the app.

Each user has their own isolated data — purchases, sales, and settings are not
visible to other users. Self-registration on the Cognito hosted UI is disabled.

---

## 2. Architecture

### Overview

```
Internet
    │
    ▼
Elastic IP  (static public IP)
    │
    ▼
EC2 t3.micro  (Ubuntu 22.04, eu-central-1)
├── Nginx          — reverse proxy, serves static files
├── Gunicorn       — Python WSGI server (3 workers)
├── Django         — business logic, REST API, HTML shell
└── PostgreSQL 14  — local database (no RDS = free forever)

AWS Cognito   — user authentication (hosted login UI + JWT tokens)
AWS IAM       — EC2 instance role, admin user
AWS VPC       — isolated network, public subnet, security groups
```

Everything runs on a single EC2 instance. This keeps costs at zero (free tier)
and complexity low for a single-shop deployment.

### Request flow

```
Browser
  │
  ├── GET /                    → Nginx → Gunicorn → Django (serves index.html SPA shell)
  ├── GET /static/...          → Nginx serves files directly (no Django involved)
  ├── GET /auth/login/         → Django → redirect to Cognito hosted UI
  ├── GET /auth/callback/      → Django exchanges auth code for tokens, sets session
  ├── GET/POST /auth/register/ → Public registration form (no login required)
  ├── GET /auth/admin/pending/ → Admin approval panel (staff login required)
  └── GET/POST /api/...        → Django REST Framework (requires session auth)
```

### Authentication flow

```
1. User visits http://localhost:8000
         │
         ▼
2. Django sees no session → builds this URL and redirects:
   https://mitumba-shop-yourname.auth.eu-central-1.amazoncognito.com/login
   ?response_type=code
   &client_id=1fabgguo8k5krsdpsc9b4pbfgp
   &redirect_uri=http://localhost:8000/auth/callback/
         │
         ▼
3. AWS serves the Cognito hosted login page (AWS servers, AWS HTML/CSS)
   User types email + password
         │
         ▼
4. Cognito verifies credentials
   Generates a one-time authorization code
   Redirects browser to:
   http://localhost:8000/auth/callback/?code=abc123
         │
         ▼
5. Django receives the code at /auth/callback/
   Makes a server-to-server POST to Cognito:
   POST https://...amazoncognito.com/oauth2/token
   { code: abc123, client_id: ..., client_secret: ... }
         │
         ▼
6. Cognito returns tokens (id_token, access_token, refresh_token)
   Django validates the JWT signature
   Creates/finds the User record in PostgreSQL
   Sets a Django session cookie
         │
         ▼
7. Browser is now logged in, redirected to /
   All subsequent API calls include the session cookie automatically
```

### User registration flow

```
1. New user visits /auth/register/
   Fills in name, email, phone → submitted to Django
         │
         ▼
2. Django saves a PendingUser record (status: pending)
   Page shows "Application received — await email"
         │
         ▼
3. Admin visits /auth/admin/pending/
   Reviews the list, confirms payment out-of-band (phone, bank transfer, etc.)
   Clicks Approve
         │
         ▼
4. Django calls Cognito AdminCreateUser API (using EC2 IAM role — no keys needed)
   Cognito creates the account + emails a temporary password to the user
   PendingUser record updated to status: approved
         │
         ▼
5. User receives the email, visits /auth/login/
   Logs in with the temporary password
   Cognito forces a password change on first sign-in
```

Self-registration via the Cognito hosted UI is disabled
(`allow_admin_create_user_only = true`). Only the admin can create accounts.

**Why Cognito's hosted UI:** AWS handles the login page, password hashing,
brute-force protection, email verification, password reset, and MFA — all for
free, without writing any of that code.

**What you can and cannot control:**
- The hosted UI page lives on AWS servers — you don't control its HTML structure
- You can upload custom CSS to Cognito to restyle it (change colors, fonts)
- For full design control, replace the hosted UI with a custom Django login form
  that calls Cognito's API directly (more work, full flexibility)

### Technology stack

| Layer | Technology | Why |
|---|---|---|
| Web server | Nginx 1.18 | Fast static file serving, reverse proxy |
| App server | Gunicorn 26 | Production-grade Python WSGI server |
| Framework | Django 4.x + Django REST Framework | Battle-tested, built-in admin, session auth |
| Database | PostgreSQL 14 | Reliable, free on-instance (no RDS costs) |
| Auth | AWS Cognito | Hosted UI, JWT, password reset — zero code to maintain |
| Infrastructure | Terraform 1.5+ | Reproducible, version-controlled infra |
| OS | Ubuntu 22.04 LTS | Long-term support |
| Cloud | AWS eu-central-1 (Frankfurt) | Free tier, EU data residency |

### Cost

| Service | Free tier | After free tier |
|---|---|---|
| EC2 t3.micro | 750 h/month (12 months) | ~$8.50/month |
| Elastic IP | Free while attached | $0.005/h if unattached |
| Cognito | 50,000 MAU (no expiry) | $0.0055/MAU |
| Data transfer | 1 GB/month out | $0.09/GB |
| **Total (free tier)** | **~$0** | **~$10/month** |

---

## 3. Infrastructure — Terraform

### Directory structure

```
infrastructure/
├── modules/
│   ├── networking/   # VPC, subnet, internet gateway, security group
│   ├── compute/      # EC2 instance, Elastic IP, SSH key, bootstrap script
│   ├── cognito/      # Cognito user pool, hosted UI, app client
│   └── iam/          # EC2 instance role, admin IAM user
└── environments/
    └── production/   # Composes all four modules; all config lives here
```

Each module is independent. All account-specific values are variables — no
hardcoded account IDs, regions, or secrets anywhere in module code.

### Module dependency graph

```
iam ←─────────────────────────────────────────────┐
networking ←──────────────────────────────────────┤
cognito ←─────────────────────────────────────────┤
                                                   └── compute
```

### Prerequisites

```bash
# Install Terraform (macOS)
brew install terraform
terraform --version   # must be ≥ 1.5

# Install AWS CLI
brew install awscli
aws --version
```

### Step 1 — Create AWS credentials

1. Open the [AWS IAM console](https://console.aws.amazon.com/iam) and sign in as root.
2. Go to **Users** → **Create user** → name it `terraform-admin`.
3. Attach policy **AdministratorAccess** directly.
4. Open the user → **Security credentials** tab → **Create access key**.
5. Choose **CLI** use case → copy both the Access Key ID and Secret Access Key.

> Never commit these values to git. Never use the root account's access key.

```bash
aws configure --profile mitumba-prod
# AWS Access Key ID:     AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region:        eu-central-1
# Default output format: json

export AWS_PROFILE=mitumba-prod

# Verify
aws sts get-caller-identity --profile mitumba-prod
```

### Step 2 — Generate an SSH key pair

```bash
# Check if you already have one
ls ~/.ssh/id_ed25519.pub

# If not, generate one (press Enter 3 times — no passphrase)
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519

# Get the public key — paste this into terraform.tfvars
cat ~/.ssh/id_ed25519.pub
```

> If you forget the passphrase you cannot recover it — you must generate a new
> key, delete the old AWS key pair, and replace the EC2 instance.

### Step 3 — Configure terraform.tfvars

```bash
cd infrastructure/environments/production
cp terraform.tfvars.example terraform.tfvars
```

Key settings to fill in:

```hcl
aws_region            = "eu-central-1"
project_name          = "mitumba"
owner_email           = "your@email.com"

# Your public IP — find it with: curl -s https://checkip.amazonaws.com
ssh_allowed_cidrs     = ["YOUR_IP/32"]

# Paste output of: cat ~/.ssh/id_ed25519.pub
ssh_public_key        = "ssh-ed25519 AAAA..."

# Generate: python -c "import secrets; print(secrets.token_urlsafe(50))"
django_secret_key     = "..."

# Strong random password for PostgreSQL
db_password           = "..."

# Must be globally unique across all AWS accounts
cognito_domain_prefix = "mitumba-shop-yourname"

# Your app domain (update after you have a real domain)
app_domain            = "shop.example.com"

# Allow localhost for SSH tunnel access during development
cognito_extra_callback_urls = [
  "http://localhost:8000/auth/callback/"
]
```

### Step 4 — Deploy

```bash
cd infrastructure/environments/production

terraform init      # download providers
terraform plan      # preview — no changes applied yet
terraform apply     # deploy everything (~3 minutes)
```

After apply:

```bash
terraform output server_ip
terraform output cognito_user_pool_id
terraform output cognito_app_client_id
terraform output -raw cognito_app_client_secret
```

### Common Terraform operations

```bash
# Update a single resource (e.g. replace EC2 instance after SSH key change)
terraform apply -replace="module.compute.aws_instance.app"

# Delete a stale AWS key pair before re-applying
aws ec2 delete-key-pair --key-name mitumba-key --region eu-central-1

# Destroy everything
terraform destroy
```

### Migrating to a different AWS account

Only `terraform.tfvars` needs to change — no module code required:

1. Create an IAM user in the new account and run `aws configure`
2. Update `terraform.tfvars`: `aws_region`, `cognito_domain_prefix`, `ssh_allowed_cidrs`, `owner_email`
3. Run `terraform init && terraform apply`

### Bulk-delete remaining AWS resources

If anything survives `terraform destroy`:

```bash
brew install gruntwork-io/tap/cloud-nuke
cloud-nuke aws --region eu-central-1 --dry-run   # preview first
cloud-nuke aws --region eu-central-1             # then delete
```

---

## 4. Backend — Django

### Directory structure

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py         # Shared settings (all environments)
│   │   ├── production.py   # EC2 production (reads .env from repo root)
│   │   └── development.py  # Local dev
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # Gunicorn entrypoint
├── apps/
│   ├── authentication/     # Cognito OIDC login, UserProfile, PendingUser models
│   ├── shop_settings/      # Per-user shop config + product categories
│   ├── purchases/          # Purchase records
│   ├── sales/              # Sale records + line items
│   ├── dashboard/          # Aggregated dashboard data
│   └── finance/            # Monthly P&L + stock levels
├── templates/
│   ├── index.html          # Single-page app HTML shell (authenticated users)
│   ├── register.html       # Public registration form
│   └── admin_pending_users.html  # Admin approval panel
├── static/
│   ├── css/style.css
│   └── js/app.js
└── requirements.txt
```

### Database tables

| Table | App | Description |
|---|---|---|
| `auth_user` | Django built-in | User accounts |
| `auth_user_profile` | authentication | Cognito `sub` UUID + stored tokens |
| `auth_pending_user` | authentication | Registration requests awaiting admin approval |
| `shop_settings` | shop_settings | Per-user shop configuration |
| `shop_product_category` | shop_settings | Up to 10 categories per user |
| `purchase` | purchases | Stock acquisitions (denormalised for performance) |
| `sale` | sales | Sale records |
| `sale_item` | sales | Individual items within a sale |

### API endpoints

**Settings**

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/settings/` | Get user's shop settings |
| `PUT` | `/api/settings/` | Update settings |

**Purchases**

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/purchases/` | List all purchases |
| `POST` | `/api/purchases/` | Create a purchase |
| `DELETE` | `/api/purchases/<id>/` | Delete a purchase |

**Sales**

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/sales/` | List all sales |
| `POST` | `/api/sales/` | Create a sale (with nested items) |
| `DELETE` | `/api/sales/<id>/` | Delete a sale |

**Dashboard / Finance / Stock**

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/dashboard/` | Current month summary |
| `GET` | `/api/finance/?year=&month=` | Monthly P&L breakdown |
| `GET` | `/api/finance/stock/` | Current stock levels |

### First-time backend deployment

The EC2 bootstrap script (`user_data.sh`) runs automatically on first boot and
handles: package installation, PostgreSQL setup, Python venv at `/opt/mitumba/venv`,
Nginx config, and the systemd `mitumba.service`. Wait for it to finish before
proceeding (~2 min):

```bash
# SSH in
ssh -i ~/.ssh/id_ed25519 ubuntu@<server-ip>

# Confirm bootstrap finished
sudo tail -3 /var/log/mitumba-bootstrap.log
# Should end with: === Bootstrap complete ===
```

**Update `/opt/mitumba/.env`** (bootstrap writes it with Terraform values, but
two lines need fixing for SSH-tunnel access):

```bash
sudo nano /opt/mitumba/.env
```

Change/add:
```
ALLOWED_HOSTS=<app_domain>,localhost
APP_DOMAIN=http://localhost:8000
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

Also replace `DJANGO_SECRET_KEY` if it still shows the placeholder from
`terraform.tfvars` — generate a real one:
```bash
sudo /opt/mitumba/venv/bin/python -c \
  "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Clone the repo and run the deploy script:**

```bash
git clone https://github.com/robikus/Mitumbashopmanager2.git ~/Mitumbashopmanager2
bash ~/Mitumbashopmanager2/scripts/deploy.sh
```

`scripts/deploy.sh` handles everything in one step:
- Links `backend/` into `/opt/mitumba/backend/` (where the service expects it)
- Installs Python dependencies (including boto3)
- Copies `.env` to repo root for `manage.py` access
- Runs `migrate` (creates all database tables)
- Runs `collectstatic`
- Fixes directory permissions for Nginx
- Restarts the `mitumba` service

**Create the superuser** (needed for the admin approval panel):

```bash
sudo /opt/mitumba/venv/bin/python /opt/mitumba/backend/manage.py \
  createsuperuser --settings=config.settings.production
```

> **Important:** Migration files must be committed to git. After any model
> change, run `makemigrations` locally, commit the generated files, and push
> before deploying. The deploy script only runs `migrate` — it does not run
> `makemigrations`.

### Gunicorn systemd service

```ini
# /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn daemon for Mitumba Shop
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/Mitumbashopmanager2/backend
EnvironmentFile=/home/ubuntu/Mitumbashopmanager2/.env
RuntimeDirectory=gunicorn
ExecStart=/home/ubuntu/Mitumbashopmanager2/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn/mitumba.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

### Nginx configuration

```nginx
# /etc/nginx/sites-available/mitumba
server {
    listen 80;
    server_name <server-ip>;

    location /static/ {
        alias /home/ubuntu/Mitumbashopmanager2/backend/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn/mitumba.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Updating the app after a code change

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<server-ip>
cd ~/Mitumbashopmanager2 && git pull && bash scripts/deploy.sh
```

The deploy script handles dependency updates, migrations, staticfiles, and
service restart automatically.

---

## 5. Administration

### SSH into the server

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@63.183.43.81
```

**Troubleshooting:**

| Error | Fix |
|---|---|
| `Permission denied (publickey)` | Always pass `-i ~/.ssh/id_ed25519` explicitly |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` | Run `ssh-keygen -R 63.183.43.81` then reconnect |
| `Connection timed out` | Your IP changed — update `ssh_allowed_cidrs` in `terraform.tfvars` and run `terraform apply` |
| Forgot SSH key passphrase | Generate new key, delete old key pair in AWS, replace EC2 instance |

### Access the app in the browser

HTTPS is not set up yet — access requires an SSH tunnel:

**Terminal 1 — app:**
```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 8000:localhost:80 ubuntu@63.183.43.81 -N
```

**Terminal 2 — database (for pgAdmin):**
```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 5433:localhost:5432 ubuntu@63.183.43.81 -N
```

Open `http://localhost:8000` in your browser.

### Connect to the database with pgAdmin

1. Open the database tunnel (above)
2. Open **pgAdmin 4** → right-click Servers → Register → Server
3. Connection settings:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `mitumba_db` |
| Username | `mitumba_user` |
| Password | value of `db_password` in `terraform.tfvars` |

**If pgAdmin shows `Crypt key is missing`:**
```bash
rm -rf ~/Library/Application\ Support/pgAdmin
# Reopen pgAdmin — it will ask for a new master password
```

### Check logs

```bash
# Live Django/Gunicorn log
sudo journalctl -u gunicorn -f

# Last 50 lines
sudo journalctl -u gunicorn -n 50

# Nginx error log
sudo tail -f /var/log/nginx/error.log

# Nginx access log
sudo tail -f /var/log/nginx/access.log
```

### Check and restart services

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

sudo systemctl restart gunicorn     # after app code changes
sudo systemctl restart nginx        # after Nginx config changes
```

### Approving new users (admin panel)

The preferred way to manage users is through the built-in admin panel:

1. A new user submits their details at `http://localhost:8000/auth/register/`
2. Log in to the app, then visit `http://localhost:8000/auth/admin/pending/`
3. You will see a table of all requests with name, email, phone, and date
4. After confirming payment, click **Approve**
   - Django calls the Cognito API using the EC2 IAM role (no keys needed)
   - Cognito creates the account and emails a temporary password to the user
5. To decline a request, click **Reject** and optionally add an internal note

> The user's first login forces a password change via Cognito.

### Manage Cognito users (AWS CLI — advanced)

Use the CLI only when bypassing the admin panel (e.g. resetting a locked account):

```bash
# Set a permanent password (use single quotes — ! breaks double quotes in zsh)
aws cognito-idp admin-set-user-password \
  --user-pool-id eu-central-1_nrMzlxwlB \
  --username user@example.com \
  --password 'NewPassword123!' \
  --permanent \
  --region eu-central-1

# List users
aws cognito-idp list-users \
  --user-pool-id eu-central-1_nrMzlxwlB \
  --region eu-central-1

# Delete a user
aws cognito-idp admin-delete-user \
  --user-pool-id eu-central-1_nrMzlxwlB \
  --username user@example.com \
  --region eu-central-1
```

### Run Django management commands (on the server)

```bash
cd ~/Mitumbashopmanager2/backend
source venv/bin/activate

# Create and apply new migrations after model changes
python manage.py makemigrations --settings=config.settings.production
python manage.py migrate --settings=config.settings.production

# Re-collect static files after CSS/JS changes
python manage.py collectstatic --settings=config.settings.production

# Open Django shell
python manage.py shell --settings=config.settings.production

# Open database shell
python manage.py dbshell --settings=config.settings.production
```

### Database backup and restore

```bash
# Backup
pg_dump -U mitumba_user mitumba_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U mitumba_user mitumba_db < backup_20260614.sql
```

### Setting up HTTPS (next step)

To make the app publicly accessible without an SSH tunnel:

1. Get a domain name and point its DNS A record to `63.183.43.81`
2. Update `terraform.tfvars`: `app_domain = "yourdomain.com"`
3. Run `terraform apply` — registers the HTTPS callback URL in Cognito
4. On the server, get a free SSL certificate:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```
5. Update `~/Mitumbashopmanager2/.env`:
   ```
   APP_DOMAIN=https://yourdomain.com
   ALLOWED_HOSTS=yourdomain.com,localhost
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com
   ```
6. Re-enable SSL in `backend/config/settings/production.py`:
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_HSTS_SECONDS = 31536000
   ```
7. `sudo systemctl restart gunicorn`

### Current deployment details

| Item | Value |
|---|---|
| Server IP | `63.183.43.81` |
| Region | `eu-central-1` (Frankfurt) |
| Instance type | `t3.micro` |
| OS | Ubuntu 22.04 LTS |
| Repo on server | `~/Mitumbashopmanager2` |
| Venv | `~/Mitumbashopmanager2/backend/venv` |
| App env file | `~/Mitumbashopmanager2/.env` |
| Static files | `~/Mitumbashopmanager2/backend/staticfiles/` |
| Cognito user pool | `eu-central-1_nrMzlxwlB` |
| Cognito app client | `1fabgguo8k5krsdpsc9b4pbfgp` |
| Terraform state | `infrastructure/environments/production/terraform.tfstate` (local) |
