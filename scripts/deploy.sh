#!/bin/bash
# =============================================================================
# deploy.sh — Run this after cloning onto a new EC2 instance, or after
#             git pull to apply code updates.
#
# Usage:
#   First deployment on a new server:
#     git clone https://github.com/robikus/Mitumbashopmanager2.git ~/Mitumbashopmanager2
#     cd ~/Mitumbashopmanager2
#     bash scripts/deploy.sh
#
#   Updating existing deployment after git pull:
#     cd ~/Mitumbashopmanager2 && git pull && bash scripts/deploy.sh
#
# What this script does:
#   1. Links backend into /opt/mitumba/backend (expected by the systemd service)
#   2. Installs/updates Python dependencies into the bootstrap venv
#   3. Copies .env to repo root so manage.py can find it (for management commands)
#   4. Runs migrations (creates tables for new models)
#   5. Collects static files
#   6. Fixes directory permissions so Nginx (www-data) can serve static files
#   7. Restarts the mitumba service
# =============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="/opt/mitumba"
VENV="$APP_DIR/venv"
PYTHON="$VENV/bin/python"
MANAGE="$PYTHON $APP_DIR/backend/manage.py"

# Use "sudo env VAR=val cmd" rather than a --settings flag or plain "export":
# Django's argv parser only looks for --settings in argv[2:], so a flag placed
# before the subcommand (e.g. "manage.py --settings=X migrate") is silently
# ignored and falls back to manage.py's default (development), which reads
# .env.local instead of .env. A plain "export" also won't survive sudo's
# environment reset, so set it via "env" in the sudo call itself.
DJANGO_ENV="DJANGO_SETTINGS_MODULE=config.settings.production"

echo "=== Mitumba deploy starting ==="
echo "Repo: $REPO_DIR"

# ── 1. Link backend ──────────────────────────────────────────────────────────
if [ ! -e "$APP_DIR/backend" ]; then
  echo "--- Linking backend..."
  sudo ln -s "$REPO_DIR/backend" "$APP_DIR/backend"
else
  echo "--- Backend already linked, skipping."
fi

# ── 2. Install Python dependencies ───────────────────────────────────────────
echo "--- Installing Python dependencies..."
sudo "$VENV/bin/pip" install -q -r "$REPO_DIR/backend/requirements.txt"

# ── 3. Copy .env to repo root for manage.py ──────────────────────────────────
# production.py checks /opt/mitumba/.env first (for the service), then the
# repo root (for manual manage.py runs). Keep repo-root copy in sync.
if [ -f "$APP_DIR/.env" ] && [ ! -f "$REPO_DIR/.env" ]; then
  echo "--- Copying .env to repo root..."
  sudo cp "$APP_DIR/.env" "$REPO_DIR/.env"
  sudo chown ubuntu:www-data "$REPO_DIR/.env"
  sudo chmod 640 "$REPO_DIR/.env"
fi

# ── 4. Run database migrations ────────────────────────────────────────────────
echo "--- Running migrations..."
sudo env $DJANGO_ENV $MANAGE migrate

# ── 5. Collect static files ───────────────────────────────────────────────────
echo "--- Collecting static files..."
sudo env $DJANGO_ENV $MANAGE collectstatic --no-input

# ── 6. Fix directory permissions ──────────────────────────────────────────────
# www-data (Nginx) needs execute permission to traverse the ubuntu home dir
echo "--- Fixing permissions..."
chmod o+x /home/ubuntu
chmod o+x "$REPO_DIR"
chmod o+x "$REPO_DIR/backend"

# ── 7. Restart service ────────────────────────────────────────────────────────
echo "--- Restarting mitumba service..."
sudo systemctl restart mitumba
sudo systemctl status mitumba --no-pager -l

echo "=== Deploy complete ==="
