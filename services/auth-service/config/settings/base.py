"""
Django base settings for Book My Venue — Auth Service.

This file contains settings shared across ALL environments (dev, prod).
Environment-specific overrides live in:
  - config/settings/dev.py   (DEBUG=True, Silk profiler, CORS open)
  - config/settings/prod.py  (DEBUG=False, HTTPS, HSTS, strict CORS)

Run with:
  DJANGO_SETTINGS_MODULE=config.settings.dev  python manage.py ...
  DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py ...
"""

from datetime import timedelta
from pathlib import Path

import dj_database_url
import structlog
from decouple import config

# =============================================================================
# PATHS
# =============================================================================

# auth-service/ root (3 parents up from this file: settings/ → config/ → auth-service/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# SECURITY
# =============================================================================

# Reads from DJANGO_SECRET_KEY env var.
# dev.py and prod.py both inherit this — no hardcoded fallback in production.
SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-dev-secret-key-change-in-prod")

# DEBUG is intentionally NOT set here.
# It MUST be explicitly set in dev.py (True) or prod.py (False).

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
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    # Platform apps
    "apps.accounts",
    "apps.common",
    "apps.tenants",
]

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
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

# Redis
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

# =============================================================================
# CELERY
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
            default="postgres://user:password@localhost:5432/auth_db",
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
            "IGNORE_EXCEPTIONS": True,  # Keep running if Redis goes down
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = "accounts.User"

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("apps.accounts.api.authentication.CustomJWTCookieAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # --- Global Exception Handler ---
    "EXCEPTION_HANDLER": "apps.common.exception_handler.custom_exception_handler",
    # --- Throttling ---
    # Override per-view with throttle_classes = [LoginRateThrottle]
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",  # Anonymous endpoints (register, docs)
        "user": "200/minute",  # Authenticated endpoints (me, tenants)
        "login": "5/minute",  # Brute-force protection on login endpoint
        "resend_otp": "3/minute",  # Prevent email pumping/spam attacks
    },
}

# =============================================================================
# JWT (djangorestframework-simplejwt)
# =============================================================================

SIMPLE_JWT = {
    # Token lifetimes
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Rotate refresh token on every use (old token is blacklisted)
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # Keep last_login up-to-date automatically
    "UPDATE_LAST_LOGIN": True,
    # Signing
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    # Headers
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    # Claims — user_id claim maps to our UUID PK field
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # Token types returned in responses
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

# =============================================================================
# JWT COOKIE SETTINGS
# =============================================================================
JWT_AUTH_COOKIE = "access_token"
JWT_AUTH_REFRESH_COOKIE = "refresh_token"
JWT_AUTH_COOKIE_DOMAIN = None  # Uses request domain
JWT_AUTH_COOKIE_SECURE = False  # Override to True in prod.py (HTTPS only)
JWT_AUTH_COOKIE_HTTPONLY = True  # Prevent JS from reading cookies
JWT_AUTH_COOKIE_PATH = "/"
JWT_AUTH_COOKIE_SAMESITE = "Lax"  # Mitigates CSRF

# =============================================================================
# OPENAPI / SWAGGER (drf-spectacular)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Book My Venue — Auth Service API",
    "DESCRIPTION": (
        "Authentication, user management, tenant provisioning, "
        "membership management, and internal context validation APIs.\n\n"
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

# Shared secret used by other microservices to call internal/* endpoints.
# Set to a strong random value in production.
INTERNAL_SERVICE_API_KEY = config(
    "INTERNAL_SERVICE_API_KEY",
    default="dev-internal-api-key",
)

# =============================================================================
# PASSWORD VALIDATION
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

# Suppresses Django 3.2+ system check warning.
# Our models use explicit UUIDField PKs, but this global default is required.
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
            # We will override this formatter in dev.py vs prod.py
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

# =============================================================================
# EMAIL SETTINGS (SMTP)
# =============================================================================
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@bookmyvenue.com")

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
