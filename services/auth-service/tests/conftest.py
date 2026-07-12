"""
Root conftest.py — Shared fixtures available to ALL tests.

Fixtures defined here are automatically available in every test file
without needing an import. This is where we define our reusable
"building blocks" like authenticated users, API clients, and tokens.
"""

import pytest

# ---------------------------------------------------------------------------
# Database / Cache Cleanup
# ---------------------------------------------------------------------------
from django.core.cache import caches
from model_bakery import baker
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture(autouse=True)
def _use_locmem_cache(settings):
    """Force tests to use fast, local memory cache instead of Redis.
    Clears the cache before and after every test to prevent leakage.
    """
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
    caches["default"].clear()
    yield
    caches["default"].clear()


# ---------------------------------------------------------------------------
# API Client Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    """An unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def authenticated_client(verified_user):
    """
    An API client that has already logged in.
    JWT access + refresh tokens are set as HttpOnly cookies
    on the client, exactly how a real browser would send them.
    """
    client = APIClient()
    refresh = RefreshToken.for_user(verified_user)
    client.cookies["access_token"] = str(refresh.access_token)
    client.cookies["refresh_token"] = str(refresh)
    return client


# ---------------------------------------------------------------------------
# User Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_password():
    """The raw password used for test users (before hashing)."""
    return "TestPass123!"


@pytest.fixture
def unverified_user(user_password):
    """A user who has registered but NOT verified their email OTP."""
    return baker.make(
        "accounts.User",
        email="unverified@test.com",
        full_name="Unverified User",
        is_verified=False,
        is_active=True,
        _fill_optional=False,
        password=user_password,
    )


@pytest.fixture
def verified_user(db, user_password):
    """
    A user who has completed registration AND email verification.
    Uses create_user() so the password is properly hashed.
    """
    from apps.accounts.models import User

    return User.objects.create_user(
        email="verified@test.com",
        password=user_password,
        full_name="Verified User",
        is_verified=True,
        is_active=True,
    )


@pytest.fixture
def inactive_user(db, user_password):
    """A user whose account has been deactivated by an admin."""
    from apps.accounts.models import User

    return User.objects.create_user(
        email="inactive@test.com",
        password=user_password,
        full_name="Inactive User",
        is_verified=True,
        is_active=False,
    )
