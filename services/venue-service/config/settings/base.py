"""
Django base settings for Book My Venue — Venue Service.

This file contains settings shared across ALL environments (dev, prod).
Environment-specific overrides live in:
  - config/settings/dev.py   (DEBUG=True, Silk profiler, CORS open)
  - config/settings/prod.py  (DEBUG=False, HTTPS, HSTS, strict CORS)

Run with:
  DJANGO_SETTINGS_MODULE=config.settings.dev  python manage.py ...
  DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py ...
"""

from pathlib import Path

import dj_database_url
import structlog
from decouple import config

# =============================================================================
# PATHS
# =============================================================================

# venue-service/ root (3 parents up from this file: settings/ → config/ → venue-service/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# SECURITY
# =============================================================================

SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-dev-secret-key-change-in-prod")

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="",
    cast=lambda v: [h.strip() for h in v.split(",") if h.strip()],
)

INSTALLED_APPS = [
    # Standard Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-Party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    # Platform apps
    "apps.common",
    "apps.venues",
]

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    "bmv_libraries.infrastructure.observability.middleware.CorrelationIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =============================================================================
# URLS & WSGI/ASGI
# =============================================================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# REDIS / CACHE
# =============================================================================

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

# =============================================================================
# CELERY (reserved for future async tasks like image processing)
# =============================================================================
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": dj_database_url.config(
        default=config(
            "DATABASE_URL",
            default="postgres://user:password@localhost:5432/venue_db",
        ),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# =============================================================================
# CACHE & SESSION BACKEND
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("apps.common.authentication.InternalJWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "EXCEPTION_HANDLER": "apps.common.exception_handler.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "300/minute",
    },
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
}

# =============================================================================
# OPENAPI / SWAGGER (drf-spectacular)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Book My Venue — Venue Service API",
    "DESCRIPTION": (
        "Venue management, image uploads, categories, amenities, and policies.\n\n"
        "**Internal endpoints** (`/internal/*`) require `X-Internal-API-Key` header."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/|/internal/",
}

# =============================================================================
# INTERNAL SERVICE SECURITY
# =============================================================================

INTERNAL_SERVICE_API_KEY = config(
    "INTERNAL_SERVICE_API_KEY",
    default="dev-internal-api-key",
)

# Auth Service URL for cross-service JWT validation
AUTH_SERVICE_URL = config(
    "AUTH_SERVICE_URL",
    default="http://auth-service:8001",
)

# =============================================================================
# STORAGE BACKEND (Strategy Pattern)
# =============================================================================
# Swap this single setting to migrate from Cloudinary to S3 in production.
# Options:
#   - "apps.common.storage.cloudinary_backend.CloudinaryStorageBackend"
#   - "apps.common.storage.s3_backend.S3StorageBackend"

STORAGE_BACKEND = config(
    "STORAGE_BACKEND",
    default="apps.common.storage.cloudinary_backend.CloudinaryStorageBackend",
)

# Cloudinary credentials (only needed when STORAGE_BACKEND is Cloudinary)
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME", default="")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY", default="")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET", default="")

# =============================================================================
# PASSWORD VALIDATION (required by Django even without custom User model)
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# =============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# LOGGING (Structlog Base Config)
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "console_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console_formatter",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
