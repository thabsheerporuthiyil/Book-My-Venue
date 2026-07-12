"""
Development settings for Book My Venue — Venue Service.

Extends base.py with dev-only tooling:
  - DEBUG on
  - CORS open (all origins)
  - django-silk SQL profiler

Usage:
  DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# CORE
# =============================================================================

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# =============================================================================
# CORS
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# SILK PROFILER (dev only)
# =============================================================================

if "silk" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS.append("silk")  # noqa: F405

if "silk.middleware.SilkyMiddleware" not in MIDDLEWARE:  # noqa: F405
    MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")  # noqa: F405

SILKY_PYTHON_PROFILER = True
SILKY_ANALYZE_QUERIES = True

# =============================================================================
# LOGGING (Dev Override)
# =============================================================================

LOGGING["handlers"]["console"]["formatter"] = "console_formatter"  # noqa: F405
