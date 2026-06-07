"""
Production settings — loaded on the EC2 server.
Reads all secrets from /opt/mitumba/.env via python-dotenv.
"""

import os
import dj_database_url
from dotenv import load_dotenv
from .base import *  # noqa: F401, F403

# Load .env from the parent of the backend directory
load_dotenv(BASE_DIR.parent / ".env")  # noqa: F405

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# ── Database (parsed from DATABASE_URL) ───────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ── Security ──────────────────────────────────────────────────────────────────
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── CORS ──────────────────────────────────────────────────────────────────────
# Not needed for a same-origin SPA; keep restrictive.
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = False
