# Deployment Progress

## Current state (2026-06-14)

The app is **fully working** via SSH tunnel:
- Login via AWS Cognito works
- Purchases can be saved to the database
- CSS/static files load correctly
- All database tables created and migrated

The remaining items are production hardening (HTTPS, domain, migrations in git).

---

## How to access the app

SSL is not set up yet. Access requires an SSH tunnel. Open **three terminals**:

**Terminal 1 — app tunnel:**
```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 8000:localhost:80 ubuntu@63.183.43.81 -N
```

**Terminal 2 — pgAdmin tunnel (optional):**
```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 5433:localhost:5432 ubuntu@63.183.43.81 -N
```

**Terminal 3 — server shell:**
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@63.183.43.81
```

Then open `http://localhost:8000` in your browser and log in with:
- Email: `polakovic.robert@gmail.com`
- Password: the one you set via Cognito CLI

**pgAdmin connection:** `localhost:5433`, database `mitumba_db`, user `mitumba_user`,
password `CHANGE_ME_use_a_strong_random_password_here_min20chars`

---

## Infrastructure (all done)

- Terraform deployed: VPC, subnet, security group, EC2 t3.micro, Elastic IP, Cognito, IAM
- Server IP: `63.183.43.81`
- Region: `eu-central-1` (Frankfurt)
- Terraform state: local at `infrastructure/environments/production/terraform.tfstate`
- Cognito user pool: `eu-central-1_nrMzlxwlB`
- Cognito app client: `1fabgguo8k5krsdpsc9b4pbfgp`
- Cognito domain: `https://mitumba-shop-yourname.auth.eu-central-1.amazoncognito.com`

---

## Server state

| Component | Status | Details |
|---|---|---|
| Nginx 1.18 | running | `/etc/nginx/sites-available/mitumba` |
| Gunicorn | running | systemd service, socket `/run/gunicorn/mitumba.sock` |
| PostgreSQL 14 | running | db `mitumba_db`, user `mitumba_user` |
| Django | deployed | repo at `~/Mitumbashopmanager2`, venv at `~/Mitumbashopmanager2/backend/venv` |
| Static files | working | collected to `~/Mitumbashopmanager2/backend/staticfiles/` |
| Migrations | applied | all apps: auth, authentication, purchases, sales, shop_settings |
| `.env` | at `~/Mitumbashopmanager2/.env` | contains DB URL, Cognito secrets, Django secret key |

---

## Known issues / next steps

### 1. Commit migrations to git (important)
App migrations were created on the server but not yet committed. Do this soon or
they'll be lost if the server is recreated:

```bash
# From your laptop, copy migrations from server
scp -i ~/.ssh/id_ed25519 -r ubuntu@63.183.43.81:~/Mitumbashopmanager2/backend/apps/*/migrations ./backend/apps/

# Then commit
git add backend/apps/*/migrations/
git commit -m "Add initial migrations for all apps"
git push
```

### 2. Set up HTTPS + real domain (needed for production)
Currently HTTP only — Cognito won't allow the server IP as a callback URL over
HTTP (only localhost is allowed). To go fully public:

1. Get a domain name (e.g. buy one or use a free one)
2. Point DNS A record to `63.183.43.81`
3. Update `terraform.tfvars`: set `app_domain = "yourdomain.com"`
4. Run `terraform apply` — registers the HTTPS callback URL in Cognito
5. On the server: `sudo certbot --nginx -d yourdomain.com`
6. Update `.env`: `APP_DOMAIN=https://yourdomain.com`, update `ALLOWED_HOSTS`
7. Re-enable SSL settings in `backend/config/settings/production.py`:
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_HSTS_SECONDS = 31536000
   ```

### 3. Finance app has no model
`apps/finance` was skipped by `makemigrations` — no models defined yet.

### 4. Django secret key not backed up
The `DJANGO_SECRET_KEY` in `.env` on the server was generated manually.
It is NOT in version control — if the server is destroyed, all sessions are
invalidated. Consider storing it in AWS Secrets Manager or at minimum note it
somewhere safe.

---

## Bugs fixed during deployment

| Bug | Fix |
|---|---|
| `SECURE_SSL_REDIRECT=True` broke HTTP access | Disabled in `production.py` |
| `.env` loaded after `base.py` → `DJANGO_SECRET_KEY` missing | Moved `load_dotenv()` before `from .base import *` |
| EC2 instance type `t2.micro` not free-tier in Frankfurt | Changed to `t3.micro` |
| SSH key had forgotten passphrase | Regenerated key, replaced EC2 instance |
| App migrations not created | Ran `makemigrations` with explicit app names |
| POST requests returning 403 (CSRF) | Added `CSRF_TRUSTED_ORIGINS` for localhost tunnel |
| Nginx security group description had em dash | Replaced with regular hyphen |
| Gunicorn socket path mismatch with Nginx | Aligned both to `mitumba.sock` |

---

## Useful commands

```bash
# Restart app after code change (on server)
cd ~/Mitumbashopmanager2 && git pull
sudo systemctl restart gunicorn

# View live app logs
sudo journalctl -u gunicorn -f

# View Nginx errors
sudo tail -f /var/log/nginx/error.log

# Django management commands
cd ~/Mitumbashopmanager2/backend
source venv/bin/activate
python manage.py <command> --settings=config.settings.production

# Reset a Cognito user password (on laptop)
aws cognito-idp admin-set-user-password \
  --user-pool-id eu-central-1_nrMzlxwlB \
  --username polakovic.robert@gmail.com \
  --password 'YourPassword123!' \
  --permanent \
  --region eu-central-1
```
