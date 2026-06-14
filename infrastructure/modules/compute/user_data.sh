#!/bin/bash
# =============================================================================
# user_data.sh  —  EC2 bootstrap script for Mitumba Shop Manager
#
# Runs once on first boot as root.  Installs and configures:
#   - Ubuntu package updates
#   - Python 3.11 + virtualenv
#   - PostgreSQL 14 (local, no RDS to stay in free tier)
#   - Nginx (reverse proxy)
#   - Gunicorn (WSGI server managed by systemd)
#   - Certbot (Let's Encrypt TLS — requires a real domain in DNS)
#
# Template variables filled by Terraform templatefile():
#   ${db_name}      PostgreSQL database name
#   ${db_user}      PostgreSQL role name
#   ${db_password}  PostgreSQL password (use a strong secret in tfvars)
#   ${app_domain}   Fully-qualified domain name (e.g. app.example.com)
#   ${django_secret_key}  Django SECRET_KEY
#   ${cognito_domain}     Cognito hosted UI domain prefix
#   ${cognito_region}     AWS region of the Cognito user pool
#   ${cognito_user_pool_id}
#   ${cognito_app_client_id}
#   ${cognito_app_client_secret}
# =============================================================================

set -euo pipefail
exec > /var/log/mitumba-bootstrap.log 2>&1

echo "=== Mitumba bootstrap starting ==="
date

# ── System packages ─────────────────────────────────────────────────────────
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y \
  python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib \
  nginx \
  certbot python3-certbot-nginx \
  git curl unzip

# ── PostgreSQL ───────────────────────────────────────────────────────────────
systemctl enable postgresql
systemctl start postgresql

# Create role and database idempotently
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${db_user}'" \
  | grep -q 1 || sudo -u postgres psql -c \
  "CREATE USER ${db_user} WITH ENCRYPTED PASSWORD '${db_password}';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${db_name}'" \
  | grep -q 1 || sudo -u postgres psql -c \
  "CREATE DATABASE ${db_name} OWNER ${db_user};"

sudo -u postgres psql -c \
  "GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${db_user};"

# Restrict PostgreSQL to localhost only (default Ubuntu config already does
# this, but make it explicit)
PG_HBA="/etc/postgresql/14/main/pg_hba.conf"
if [ -f "$PG_HBA" ]; then
  sed -i 's/^host.*all.*all.*0\.0\.0\.0\/0.*md5/# disabled remote access/' "$PG_HBA"
  systemctl reload postgresql
fi

# ── Application directory ────────────────────────────────────────────────────
APP_DIR=/opt/mitumba
mkdir -p "$APP_DIR"

# Python virtual environment
python3.11 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip

# Install Python dependencies (same list as requirements.txt)
"$APP_DIR/venv/bin/pip" install \
  django==4.2.* \
  djangorestframework==3.14.* \
  psycopg2-binary \
  "python-jose[cryptography]" \
  requests \
  gunicorn \
  django-cors-headers \
  whitenoise \
  python-dotenv \
  boto3

# ── Environment file ─────────────────────────────────────────────────────────
# Written here so the systemd service can source it.  Update this file
# after deploying new app code if any secrets change.
cat > "$APP_DIR/.env" << 'ENVEOF'
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=${django_secret_key}
DATABASE_URL=postgresql://${db_user}:${db_password}@localhost:5432/${db_name}
ALLOWED_HOSTS=${app_domain},localhost
COGNITO_REGION=${cognito_region}
COGNITO_USER_POOL_ID=${cognito_user_pool_id}
COGNITO_APP_CLIENT_ID=${cognito_app_client_id}
COGNITO_APP_CLIENT_SECRET=${cognito_app_client_secret}
COGNITO_DOMAIN=https://${cognito_domain}.auth.${cognito_region}.amazoncognito.com
APP_DOMAIN=https://${app_domain}
CSRF_TRUSTED_ORIGINS=http://localhost:8000
ENVEOF

chown -R www-data:www-data "$APP_DIR"
chmod 640 "$APP_DIR/.env"

# Pre-create Gunicorn log files so www-data can write to them on first start
touch /var/log/mitumba-access.log /var/log/mitumba-error.log
chown www-data:www-data /var/log/mitumba-access.log /var/log/mitumba-error.log

# ── Systemd service ──────────────────────────────────────────────────────────
cat > /etc/systemd/system/mitumba.service << 'SVCEOF'
[Unit]
Description=Mitumba Shop Manager (Gunicorn)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/mitumba/backend
RuntimeDirectory=gunicorn
EnvironmentFile=/opt/mitumba/.env
ExecStart=/opt/mitumba/venv/bin/gunicorn \
  --bind unix:/run/gunicorn/mitumba.sock \
  --workers 2 \
  --timeout 60 \
  --access-logfile /var/log/mitumba-access.log \
  --error-logfile /var/log/mitumba-error.log \
  config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
# Service starts after app code is deployed; enable it now so it auto-starts
systemctl enable mitumba

# ── Nginx ─────────────────────────────────────────────────────────────────────
cat > /etc/nginx/sites-available/mitumba << NGINXEOF
server {
    listen 80;
    server_name ${app_domain};

    # Static assets served directly by Nginx (much faster than Gunicorn)
    location /static/ {
        alias /opt/mitumba/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy everything else to Gunicorn via Unix socket
    location / {
        proxy_pass http://unix:/run/gunicorn/mitumba.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 90;
    }
}
NGINXEOF

# Disable default site and enable ours
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/mitumba /etc/nginx/sites-enabled/mitumba

nginx -t
systemctl enable nginx
systemctl restart nginx

echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Deploy app code to /opt/mitumba/backend/"
echo "  2. Run: cd /opt/mitumba/backend && ../venv/bin/python manage.py migrate"
echo "  3. Run: ../venv/bin/python manage.py collectstatic --no-input"
echo "  4. Run: systemctl start mitumba"
echo "  5. Obtain TLS cert: certbot --nginx -d ${app_domain}"
date
