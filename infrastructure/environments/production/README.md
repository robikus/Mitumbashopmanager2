# Production Environment

Composes the four infrastructure modules into a complete AWS deployment.

## AWS credentials setup

Before running Terraform you need AWS credentials on your laptop. Follow the steps below once per AWS account.

### Step 1 — Create an IAM user in the AWS Console

1. Open [https://console.aws.amazon.com/iam](https://console.aws.amazon.com/iam) and sign in as the **root** account (or any existing admin).
2. In the left sidebar go to **Users** → **Create user**.
3. Enter a name (e.g. `terraform-admin`) and click **Next**.
4. On the permissions screen choose **Attach policies directly** and tick **AdministratorAccess**, then click **Next** → **Create user**.
5. Open the user you just created, go to the **Security credentials** tab, scroll to **Access keys** and click **Create access key**.
6. Choose use case **Command Line Interface (CLI)**, tick the confirmation checkbox, click **Next** → **Create access key**.
7. **Copy both values now** — the Secret Access Key is shown only once:
   - Access Key ID (looks like `AKIAIOSFODNN7EXAMPLE`)
   - Secret Access Key (looks like `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

> **Security tip:** Never commit these values to git. Never use the root account's access key — always create a dedicated IAM user.

---

### Step 2 — Install the AWS CLI (if not already installed)

```bash
# macOS
brew install awscli

# Verify
aws --version
```

For other platforms see [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

---

### Step 3 — Configure credentials on your laptop

**Option A — named profile (recommended, keeps credentials isolated per account)**

```bash
aws configure --profile mitumba-prod
# AWS Access Key ID [None]:     AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name [None]:   eu-central-1        # match your terraform.tfvars
# Default output format [None]: json
```

Then tell Terraform to use that profile — either export the variable in your shell session:

```bash
export AWS_PROFILE=mitumba
```

or add it permanently to `~/.zshrc` / `~/.bashrc`:

```bash
echo 'export AWS_PROFILE=mitumba' >> ~/.bashrc
source ~/.bashrc
```

**Option B — default profile (simpler, but replaces any existing default)**

```bash
aws configure
# same prompts as above
```

Credentials are stored in `~/.aws/credentials` and region/output in `~/.aws/config`.

---

### Step 4 — Verify credentials work

```bash
aws sts get-caller-identity --profile mitumba-prod
# Expected output:
# {
#     "UserId": "AIDAIOSFODNN7EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/terraform-admin"
# }
```

If you see your Account ID and user ARN, credentials are working and Terraform can use them.

---

### Step 5 — Reference the profile in Terraform (already wired in)

The Terraform provider in this project reads `AWS_PROFILE` from the environment, so once you export it (Step 3) no changes to `.tf` files are needed.

---

### Rotating or revoking credentials

When you no longer need an access key (or suspect it was exposed):

1. AWS Console → IAM → Users → `terraform-admin` → **Security credentials** tab.
2. Click **Deactivate** next to the old key, verify everything still works, then click **Delete**.
3. Run `aws configure --profile mitumba-prod` again with the new key values.

---

## SSH keys — how they work and how to access the server

### How SSH key authentication works

SSH uses a **key pair** — two mathematically linked files:

| File | Location | What it does |
|---|---|---|
| Private key | `~/.ssh/id_ed25519` | Stays on your laptop only. Never share it. |
| Public key | `~/.ssh/id_ed25519.pub` | Placed on the server. Safe to share freely. |

When you SSH in, your laptop uses the private key to sign a challenge. The server checks the signature against the public key it has on file. If they match, you're in — no password needed and no secret travels over the network.

Terraform puts your public key on the EC2 instance at launch time (via the `aws_key_pair` resource). It ends up in `/home/ubuntu/.ssh/authorized_keys` on the server.

---

### Step 1 — Generate an SSH key pair (once, on your laptop)

```bash
# Check if you already have one
ls ~/.ssh/

# If id_ed25519 and id_ed25519.pub exist, skip this step.
# Otherwise generate a new pair (press Enter 3 times — no passphrase recommended):
ssh-keygen -t ed25519 -C "polakovic.robert@gmail.com" -f ~/.ssh/id_ed25519
```

> **No passphrase:** A passphrase adds extra security but means you must type it every time you SSH. For a personal dev server, skipping it is fine. If you forget the passphrase later you cannot recover it — you must generate a new key and redeploy.

---

### Step 2 — Put the public key in terraform.tfvars

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the entire output line (starts with `ssh-ed25519 AAAA...`) and paste it into `terraform.tfvars`:

```hcl
ssh_public_key = "ssh-ed25519 AAAAC3... polakovic.robert@gmail.com"
```

Then run `terraform apply` — Terraform creates the key pair on AWS and the instance boots with it installed.

---

### Step 3 — SSH into the server

Get the server IP from Terraform:

```bash
cd /Users/robi/Git/Mitumbashopmanager2/infrastructure/environments/production
terraform output server_ip
```

Connect:

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<server-ip>
```

- Username is always `ubuntu` on Ubuntu EC2 instances
- `-i ~/.ssh/id_ed25519` tells SSH which key to use (avoids confusion if you have multiple keys)
- Type `yes` the first time to accept the server's fingerprint

---

### Troubleshooting SSH

**`Permission denied (publickey)`**
- Wrong key being used — always pass `-i ~/.ssh/id_ed25519` explicitly
- Key in `terraform.tfvars` doesn't match the key on your laptop — check with:
  ```bash
  cat ~/.ssh/id_ed25519.pub
  grep ssh_public_key terraform.tfvars
  ```
  If they differ, update `terraform.tfvars` and run:
  ```bash
  aws ec2 delete-key-pair --key-name mitumba-key --region eu-central-1
  terraform apply -replace="module.compute.aws_instance.app"
  ```
  The instance IP will change — run `terraform output server_ip` again.

**`WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED`**
- The server was recreated (new instance, new host key). This is expected.
- Clear the old entry and reconnect:
  ```bash
  ssh-keygen -R <server-ip>
  ssh -i ~/.ssh/id_ed25519 ubuntu@<server-ip>
  ```

**`Connection timed out`**
- Your IP has changed (ISPs reassign dynamic IPs). Update `terraform.tfvars`:
  ```bash
  curl -s https://checkip.amazonaws.com   # get your new IP
  # update ssh_allowed_cidrs in terraform.tfvars
  terraform apply
  ```

---

## Connecting to PostgreSQL with pgAdmin

PostgreSQL runs on the server and is not exposed to the internet. The secure way to connect from your laptop is via an **SSH tunnel** — your IDE connects to a local port, and SSH forwards that traffic through your encrypted SSH connection to the server.

### Step 1 — Open the SSH tunnel

Run this in a terminal and **leave it running**:

```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 5433:localhost:5432 ubuntu@<server-ip> -N
```

- `-L 5433:localhost:5432` — maps your local port 5433 to port 5432 on the server
- `-N` — don't open a shell, just forward the port
- We use local port `5433` (not `5432`) because macOS may already have PostgreSQL running locally on 5432

Get your server IP:

```bash
cd /Users/robi/Git/Mitumbashopmanager2/infrastructure/environments/production
terraform output server_ip
```

### Step 2 — Connect pgAdmin to the tunnel

1. Open **pgAdmin 4** (Finder → Applications → pgAdmin 4)
2. Right-click **Servers** → **Register** → **Server**
3. Fill in the **General** tab:
   - Name: `Mitumba Production`
4. Fill in the **Connection** tab:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `mitumba_db` |
| Username | `mitumba_user` |
| Password | value of `db_password` in `terraform.tfvars` |

5. Click **Save** — you should see the database appear in the tree on the left.

### Troubleshooting pgAdmin

**`Crypt key is missing` error**
pgAdmin lost its master password. Reset it:

```bash
# Close pgAdmin first, then:
rm -rf ~/Library/Application\ Support/pgAdmin
```

Reopen pgAdmin — it will ask you to set a new master password from scratch.

**`Address already in use` when opening the tunnel**
Local port 5433 is taken. Use a different port (e.g. 5434):

```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 5434:localhost:5432 ubuntu@<server-ip> -N
```

Then use port `5434` in pgAdmin instead.

---

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

## Deploying the Django app

### Step 1 — Clone the repository on the server

SSH into the server, then clone the repo:

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<server-ip>

# Option A: HTTPS (public repo or with personal access token)
git clone https://github.com/<your-username>/Mitumbashopmanager2.git

# Option B: SSH (recommended — generate a key on the server and add it to GitHub)
ssh-keygen -t ed25519 -C "polakovic.robert@gmail.com" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub   # copy this and add to GitHub → Settings → SSH keys
git clone git@github.com:<your-username>/Mitumbashopmanager2.git
```

The repo clones into `~/Mitumbashopmanager2`.

---

### Step 2 — Set up Python virtual environment

Ubuntu ships without the venv module — install it first:

```bash
sudo apt install python3.10-venv -y
```

Then create the virtual environment and install dependencies:

```bash
cd ~/Mitumbashopmanager2/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You must activate the venv (`source venv/bin/activate`) every time you open a new SSH session before running any Django commands. Your prompt will show `(venv)` when it is active.

---

### Step 3 — Run Django migrations

Migrations create all the database tables in `mitumba_db`:

```bash
cd ~/Mitumbashopmanager2/backend
source venv/bin/activate
python manage.py migrate --settings=config.settings.production
```

After this you will see all tables in pgAdmin under `mitumba_db` → Schemas → public → Tables.

---

### Step 4 — Create a Django superuser

```bash
python manage.py createsuperuser --settings=config.settings.production
```

---

### Step 5 — Collect static files

```bash
python manage.py collectstatic --settings=config.settings.production
```

---

### Updating the app after a code change

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<server-ip>
cd ~/Mitumbashopmanager2
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt        # only needed if dependencies changed
python manage.py migrate --settings=config.settings.production
sudo systemctl restart gunicorn        # restart the app server
```

---

## Destroying the environment

```bash
terraform destroy
```

This deletes all resources.  The PostgreSQL data on EC2 is lost — take a
backup first (`pg_dump -U mitumba_user mitumba_db > backup.sql`).
