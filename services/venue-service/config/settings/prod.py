"""
Production settings for Book My Venue — Venue Service.

Extends base.py with production hardening:
  - DEBUG off
  - HTTPS enforcement (HSTS)
  - Strict CORS
  - Env-driven ALLOWED_HOSTS
  - Production PostgreSQL backend

Usage:
  DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py ...
"""

import dj_database_url
from decouple import config

from .base import *  # noqa: F401, F403

# =============================================================================
# CORE
# =============================================================================

DEBUG = False

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="",
    cast=lambda v: [h.strip() for h in v.split(",") if h.strip()],
)

# =============================================================================
# CORS
# =============================================================================

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda v: [o.strip() for o in v.split(",") if o.strip()],
)

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# =============================================================================
# HTTPS / HSTS
# =============================================================================
# SSL Redirection is handled by Nginx, NOT Django.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =============================================================================
# LOGGING (Prod Override)
# =============================================================================

LOGGING["handlers"]["console"]["formatter"] = "json_formatter"  # noqa: F405
