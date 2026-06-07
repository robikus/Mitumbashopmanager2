"""
Development settings — for local development only.
Reads from backend/.env.local (or falls back to environment variables).
"""

import os
import dj_database_url
from dotenv import load_dotenv
from .base import *  # noqa: F401, F403

load_dotenv(BASE_DIR / ".env.local")  # noqa: F405

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default="postgresql://mitumba_user:devpassword@localhost:5432/mitumba_dev",
        conn_max_age=0,  # close connections after each request in dev
    )
}

# Relax security for local HTTP
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Allow all origins in development (Django debug toolbar, etc.)
CORS_ALLOW_ALL_ORIGINS = True

# Show emails in the console instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
