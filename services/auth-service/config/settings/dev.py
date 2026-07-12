"""
Development settings for Book My Venue — Auth Service.

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

# Allow all origins in development — frontend runs on a different port
CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# SILK PROFILER (dev only)
# =============================================================================

# Add Silk to INSTALLED_APPS
if "silk" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS.append("silk")  # noqa: F405

# Inject Silk middleware at position 0
if "silk.middleware.SilkyMiddleware" not in MIDDLEWARE:  # noqa: F405
    MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")  # noqa: F405

# Enable deep SQL analysis and Python profiling
SILKY_PYTHON_PROFILER = True
SILKY_ANALYZE_QUERIES = True

# =============================================================================
# LOGGING (Dev Override)
# =============================================================================

# Ensure pretty console logs in development
LOGGING["handlers"]["console"]["formatter"] = "console_formatter"  # noqa: F405
