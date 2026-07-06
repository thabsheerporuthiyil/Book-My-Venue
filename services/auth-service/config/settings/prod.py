"""
Production settings for Book My Venue — Auth Service.

Extends base.py with production hardening:
  - DEBUG off
  - HTTPS enforcement (SSL redirect, HSTS)
  - Strict CORS
  - Env-driven ALLOWED_HOSTS
  - django-tenants compatible PostgreSQL backend

Usage:
  DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py ...
"""

from decouple import config

from .base import *  # noqa: F401, F403

# =============================================================================
# CORE
# =============================================================================

DEBUG = False

# Reads comma-separated list from env:
# ALLOWED_HOSTS=auth-service.bookmyvenue.com,localhost
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="",
    cast=lambda v: [h.strip() for h in v.split(",") if h.strip()],
)

# =============================================================================
# CORS
# =============================================================================

# Reads comma-separated list from env:
# CORS_ALLOWED_ORIGINS=https://bookmyvenue.com,https://app.bookmyvenue.com
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

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
JWT_AUTH_COOKIE_SECURE = True

# HSTS: tell browsers to use HTTPS for 1 year
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy header (used when behind nginx)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =============================================================================
# LOGGING (Prod Override)
# =============================================================================

# Ensure machine-readable JSON logs in production
LOGGING["handlers"]["console"]["formatter"] = "json_formatter"
