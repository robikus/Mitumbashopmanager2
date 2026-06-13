# Deployment Progress

## Current state (end of session 2026-06-14)

The app is live and accessible via SSH tunnel. Login works via AWS Cognito.
The page loads but **CSS/static files are not being served** — this is the next thing to fix.

### Infrastructure (all done)
- Terraform deployed: VPC, subnet, security group, EC2 t3.micro, Elastic IP, Cognito user pool, IAM roles
- Server IP: `63.183.43.81`
- Region: `eu-central-1` (Frankfurt)
- Terraform state: local, at `infrastructure/environments/production/terraform.tfstate`

### Server state
- OS: Ubuntu 22.04
- Nginx 1.18 — running, config at `/etc/nginx/sites-available/mitumba`
- Gunicorn — running as systemd service (`/etc/systemd/system/gunicorn.service`), socket at `/run/gunicorn/mitumba.sock`
- PostgreSQL 14 — running, database `mitumba_db`, user `mitumba_user`
- Repo cloned at: `~/Mitumbashopmanager2`
- Venv at: `~/Mitumbashopmanager2/backend/venv`
- `.env` file at: `~/Mitumbashopmanager2/.env`
- Static files collected to: `~/Mitumbashopmanager2/backend/staticfiles/`
- All migrations applied (including app-specific: authentication, purchases, sales, shop_settings)

### Cognito state
- User pool ID: `eu-central-1_nrMzlxwlB`
- App client ID: `1fabgguo8k5krsdpsc9b4pbfgp`
- Cognito domain: `https://mitumba-shop-yourname.auth.eu-central-1.amazoncognito.com`
- User created: `polakovic.robert@gmail.com`
- Allowed callback URLs: `http://localhost:8000/auth/callback/`, `https://shop.example.com/auth/callback/`

### How to access the app right now
SSL is not set up yet. Access via SSH tunnel:

```bash
# Terminal 1 — keep open
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -L 8000:localhost:80 ubuntu@63.183.43.81 -N

# Browser
http://localhost:8000
```

Login with `polakovic.robert@gmail.com` and the Cognito password you set.

---

## Known issues / next steps

### 1. Static files not loading (NEXT)
The page loads but has no CSS/JS. Nginx config serves static files from
`/home/ubuntu/Mitumbashopmanager2/backend/staticfiles/` but they may not be
accessible due to directory permissions, or the static URL paths in the HTML
don't match the Nginx location block.

**How to debug:**
```bash
# On server — check if static files exist
ls ~/Mitumbashopmanager2/backend/staticfiles/

# Check Nginx can read them
sudo -u www-data ls /home/ubuntu/Mitumbashopmanager2/backend/staticfiles/

# Check Nginx error log when browser loads page
sudo tail -f /var/log/nginx/error.log
```

**Likely fix:** Nginx (running as www-data) can't read files in /home/ubuntu.
Either change static file location or fix permissions:
```bash
chmod o+x /home/ubuntu
chmod o+x /home/ubuntu/Mitumbashopmanager2
chmod o+x /home/ubuntu/Mitumbashopmanager2/backend
```

### 2. HTTPS / SSL not set up
Currently HTTP only. Cognito won't allow adding the server IP as an HTTP
callback URL (only localhost is allowed over HTTP). To use a real domain:
1. Buy/get a domain name
2. Point DNS A record to `63.183.43.81`
3. Run: `sudo certbot --nginx -d yourdomain.com`
4. Update `terraform.tfvars`: set `app_domain` to the real domain
5. Update `.env` on server: set `APP_DOMAIN=https://yourdomain.com`
6. Update `ALLOWED_HOSTS` in `.env` to include the domain
7. Run `terraform apply` to register the new callback URL in Cognito
8. Re-enable SSL settings in `backend/config/settings/production.py`

### 3. Django secret key hardcoded in .env
The `DJANGO_SECRET_KEY` in `.env` on the server was generated manually.
It is NOT stored in Terraform or version control — don't lose it.

### 4. migrations not in git
App migrations were created on the server with `makemigrations` but not
committed to the repo. Run on laptop:
```bash
git pull   # get the migration files from server... 
# Actually: copy them from server first
scp -i ~/.ssh/id_ed25519 -r ubuntu@63.183.43.81:~/Mitumbashopmanager2/backend/apps/*/migrations ./backend/apps/
# Then commit:
git add backend/apps/*/migrations/
git commit -m "Add initial migrations for all apps"
git push
```

### 5. Finance app has no model
`apps/finance` has no `models.py` content — `makemigrations` skipped it.
Needs models defined before it can be migrated.

---

## Key file locations

| What | Where |
|---|---|
| Terraform config | `infrastructure/environments/production/` |
| Django settings | `backend/config/settings/production.py` |
| Nginx config (server) | `/etc/nginx/sites-available/mitumba` |
| Gunicorn service (server) | `/etc/systemd/system/gunicorn.service` |
| App env vars (server) | `~/Mitumbashopmanager2/.env` |
| Static files (server) | `~/Mitumbashopmanager2/backend/staticfiles/` |

## Useful commands

```bash
# SSH into server
ssh -i ~/.ssh/id_ed25519 ubuntu@63.183.43.81

# Restart app after code change
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
```
