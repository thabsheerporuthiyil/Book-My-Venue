"""
Cross-Service JWT Authentication for the Venue Service.

This service does NOT have direct access to the JWT signing key or User tables.
Authentication is fully delegated to the Auth Service via its internal API.

Flow:
    1. Extract JWT from HttpOnly cookie (or Authorization header as fallback).
    2. Extract tenant_id from X-Tenant-Id header (if present).
    3. Call Auth Service: POST http://auth-service:8001/internal/auth/validate-context/
    4. If valid → return (AuthenticatedUser, tenant_context).
    5. If invalid → raise AuthenticationFailed.

The validated user and tenant context are cached in Redis for 30 seconds
to prevent hammering the Auth Service on consecutive requests.
"""

import hashlib
import logging
from types import SimpleNamespace

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

CACHE_TTL = 30  # seconds


class AuthenticatedUser:
    """
    Lightweight user object injected into request.user after successful
    cross-service authentication. This is NOT a Django User model instance —
    the Venue Service does not have a User table.
    """

    def __init__(self, user_data, tenant_data=None):
        self.id = user_data.get("id")
        self.email = user_data.get("email")
        self.global_role = user_data.get("global_role", "USER")
        self.tenant = SimpleNamespace(**tenant_data) if tenant_data else None
        self.is_authenticated = True

    def __str__(self):
        return f"AuthenticatedUser({self.email})"


class InternalJWTAuthentication(BaseAuthentication):
    """
    DRF Authentication class that validates JWT tokens by calling the
    Auth Service's internal validation endpoint.
    """

    def authenticate(self, request):
        # 1. Extract JWT from HttpOnly cookie or Authorization header
        token = request.COOKIES.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            return None  # No credentials provided — let permission classes handle it

        # 2. Extract optional tenant context
        tenant_id = request.headers.get("X-Tenant-Id")

        # 3. Check Redis cache first (avoids redundant HTTP calls)
        cache_key = self._build_cache_key(token, tenant_id)
        cached = cache.get(cache_key)
        if cached:
            return (
                AuthenticatedUser(cached["user"], cached.get("tenant")),
                cached,
            )

        # 4. Call Auth Service internal API
        try:
            payload = {"access_token": token}
            if tenant_id:
                payload["tenant_id"] = tenant_id

            response = requests.post(
                f"{settings.AUTH_SERVICE_URL}/internal/auth/validate-context/",
                json=payload,
                headers={"X-Internal-API-Key": settings.INTERNAL_SERVICE_API_KEY},
                timeout=5,
            )
        except requests.RequestException as exc:
            logger.error("Auth service unreachable: %s", exc)
            raise AuthenticationFailed("Authentication service is unavailable.") from exc

        if response.status_code == 200:
            data = response.json()
            if data.get("valid"):
                # 5. Cache the validated context
                cache.set(cache_key, data, timeout=CACHE_TTL)
                return (
                    AuthenticatedUser(data["user"], data.get("tenant")),
                    data,
                )

        # 6. Auth failed — extract error message
        try:
            error_msg = response.json().get("message", "Invalid token.")
        except Exception:
            error_msg = "Invalid token."

        raise AuthenticationFailed(error_msg)

    def _build_cache_key(self, token, tenant_id):
        """Build a deterministic cache key from the token + tenant pair."""
        raw = f"{token}:{tenant_id or 'none'}"
        hashed = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"venue:auth:{hashed}"
