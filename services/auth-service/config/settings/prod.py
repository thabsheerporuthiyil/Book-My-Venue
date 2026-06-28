from .base import *

DEBUG = False

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="",
    cast=lambda value: [host.strip() for host in value.split(",") if host.strip()],
)

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda value: [origin.strip() for origin in value.split(",") if origin.strip()],
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("AUTH_DB_NAME"),
        "USER": config("AUTH_DB_USER"),
        "PASSWORD": config("AUTH_DB_PASSWORD"),
        "HOST": config("AUTH_DB_HOST"),
        "PORT": config("AUTH_DB_PORT", default="5432"),
    }
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True