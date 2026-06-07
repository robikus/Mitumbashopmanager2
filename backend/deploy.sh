#!/bin/bash
# =============================================================================
# deploy.sh — Deploy app code to the EC2 instance
#
# Usage:
#   ./deploy.sh <ec2-ip-or-hostname>
#
# Pre-requisites:
#   - SSH key registered in your ssh-agent or at ~/.ssh/id_rsa
#   - EC2 instance bootstrapped (user_data.sh has run to completion)
#   - DNS A record points to the Elastic IP (for Certbot to work)
#
# What it does:
#   1. rsync the backend/ directory to /opt/mitumba/backend/
#   2. Install/upgrade Python dependencies
#   3. Run Django migrations
#   4. Collect static files
#   5. Restart the Gunicorn service
# =============================================================================

set -euo pipefail

SERVER="${1:?Usage: $0 <server-ip>}"
APP_DIR="/opt/mitumba"
REMOTE_USER="ubuntu"

echo "==> Deploying to ${SERVER}"

# ── 1. Sync code ──────────────────────────────────────────────────────────────
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env*' \
  --exclude 'staticfiles/' \
  "$(dirname "$0")/" \
  "${REMOTE_USER}@${SERVER}:${APP_DIR}/backend/"

# ── 2-5. Remote steps ─────────────────────────────────────────────────────────
ssh -t "${REMOTE_USER}@${SERVER}" << REMOTE
  set -e
  cd ${APP_DIR}

  echo "-- Installing dependencies --"
  sudo ${APP_DIR}/venv/bin/pip install -r ${APP_DIR}/backend/requirements.txt -q

  echo "-- Running migrations --"
  sudo -u www-data ${APP_DIR}/venv/bin/python ${APP_DIR}/backend/manage.py migrate --settings=config.settings.production

  echo "-- Collecting static files --"
  sudo -u www-data ${APP_DIR}/venv/bin/python ${APP_DIR}/backend/manage.py collectstatic --no-input --settings=config.settings.production

  echo "-- Restarting application server --"
  sudo systemctl restart mitumba
  sleep 2
  sudo systemctl status mitumba --no-pager

  echo "==> Deploy complete!"
REMOTE
