"""
Production settings — loaded on the EC2 server.
Reads all secrets from a .env file in the repo root via python-dotenv.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Load .env before importing base so os.environ is populated when base.py runs
load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

from .base import *  # noqa: F401, F403, E402

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
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── CORS ──────────────────────────────────────────────────────────────────────
# Not needed for a same-origin SPA; keep restrictive.
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = False
