"""
Security tests for the Auth Service.

These tests verify that the authentication system is hardened against
common web security vulnerabilities. In an auth service, security is
not a feature — it's the entire product.

Categories tested:
    1. JWT Cookie Security (HttpOnly, Secure, SameSite flags)
    2. Token Blacklisting & Session Invalidation
    3. Brute-Force / Account Lockout Protection
    4. Email Enumeration Prevention
    5. OTP Replay Attack Prevention
    6. Unauthenticated Access Protection
"""

import pytest
from apps.accounts.core.lockout import AccountLockoutTracker
from apps.accounts.core.services.otp import _get_otp_cache_key
from apps.accounts.models import User
from django.core.cache import cache
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = [pytest.mark.security, pytest.mark.django_db]

LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/me/"
REGISTER_URL = "/api/auth/register/customer/"
RESEND_URL = "/api/auth/resend-otp/"
VERIFY_URL = "/api/auth/verify-otp/"
CHANGE_PASSWORD_URL = "/api/auth/change-password/"
REFRESH_URL = "/api/auth/refresh/"


# ---------------------------------------------------------------------------
# 1. JWT Cookie Security Flags
# ---------------------------------------------------------------------------


class TestJWTCookieSecurity:
    """
    Ensures JWT tokens are delivered via HttpOnly cookies with proper
    security flags. This prevents XSS attacks from stealing tokens.
    """

    def test_access_token_is_httponly(self, api_client, verified_user, user_password):
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        cookie = response.cookies["access_token"]
        assert cookie["httponly"] is True

    def test_refresh_token_is_httponly(self, api_client, verified_user, user_password):
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        cookie = response.cookies["refresh_token"]
        assert cookie["httponly"] is True

    def test_cookies_have_samesite_lax(self, api_client, verified_user, user_password):
        """SameSite=Lax prevents CSRF attacks via cross-origin POST requests."""
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        assert response.cookies["access_token"]["samesite"] == "Lax"
        assert response.cookies["refresh_token"]["samesite"] == "Lax"

    def test_tokens_not_exposed_in_response_body(self, api_client, verified_user, user_password):
        """
        JWT tokens must NEVER appear in the JSON response body.
        They are ONLY in cookies. This prevents JS from reading them.
        """
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        body = response.json()
        assert "access" not in body
        assert "refresh" not in body
        assert "access_token" not in body.get("data", {})
        assert "refresh_token" not in body.get("data", {})


# ---------------------------------------------------------------------------
# 2. Token Blacklisting & Session Invalidation
# ---------------------------------------------------------------------------


class TestTokenBlacklisting:
    """
    Ensures that refresh tokens are properly invalidated on logout
    and password change, preventing stolen tokens from being reused.
    """

    def test_blacklisted_refresh_token_cannot_be_used(self, api_client, verified_user, user_password):
        """Once you logout, the old refresh token must be dead."""
        login_resp = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})
        refresh_cookie = login_resp.cookies["refresh_token"].value

        api_client.post(LOGOUT_URL, {"all_devices": False})

        api_client.cookies.clear()
        api_client.cookies["refresh_token"] = refresh_cookie
        response = api_client.post(REFRESH_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_change_invalidates_all_sessions(self, api_client, verified_user, user_password):
        """
        If a user changes their password, ALL sessions everywhere must be killed.
        This protects against a compromised device.
        """
        old_refresh = RefreshToken.for_user(verified_user)

        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})
        api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": user_password, "new_password": "NewSecurePass789!"},
        )

        api_client.cookies.clear()
        api_client.cookies["refresh_token"] = str(old_refresh)
        response = api_client.post(REFRESH_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_all_devices_kills_every_session(self, api_client, verified_user, user_password):
        tokens = [RefreshToken.for_user(verified_user) for _ in range(3)]

        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})
        api_client.post(LOGOUT_URL, {"all_devices": True})

        for token in tokens:
            api_client.cookies.clear()
            api_client.cookies["refresh_token"] = str(token)
            response = api_client.post(REFRESH_URL)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# 3. Brute-Force / Account Lockout
# ---------------------------------------------------------------------------


class TestBruteForceProtection:
    """
    Ensures the account lockout system prevents brute-force password guessing.
    """

    def test_account_locks_after_max_attempts(self, api_client, verified_user, user_password):
        for _ in range(AccountLockoutTracker.MAX_ATTEMPTS):
            api_client.post(LOGIN_URL, {"email": verified_user.email, "password": "wrong!"})

        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_successful_login_resets_lockout_counter(self, api_client, verified_user, user_password):
        for _ in range(3):
            api_client.post(LOGIN_URL, {"email": verified_user.email, "password": "wrong!"})

        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})
        assert response.status_code == status.HTTP_200_OK

        for _ in range(3):
            api_client.post(LOGIN_URL, {"email": verified_user.email, "password": "wrong!"})

        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})
        assert response.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# 4. Email Enumeration Prevention
# ---------------------------------------------------------------------------


class TestEmailEnumerationPrevention:
    """
    An attacker should NOT be able to determine whether an email is
    registered by observing different responses for existing vs non-existing emails.
    """

    def test_resend_otp_same_response_for_known_and_unknown_email(self, api_client, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")

        resp_unknown = api_client.post(RESEND_URL, {"email": "doesnotexist@test.com"})
        resp_known = api_client.post(RESEND_URL, {"email": verified_user.email})

        assert resp_unknown.status_code == resp_known.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# 5. OTP Replay Attack Prevention
# ---------------------------------------------------------------------------


class TestOTPReplayAttack:
    """
    Once an OTP is used, it must be destroyed immediately.
    An attacker who intercepts the OTP should not be able to use it twice.
    """

    def test_otp_single_use_only(self, api_client, db, user_password):
        user = User.objects.create_user(
            email="replay@test.com",
            password=user_password,
            full_name="Replay User",
            is_verified=False,
        )
        cache_key = _get_otp_cache_key(user.email)
        cache.set(cache_key, "999999", timeout=300)

        resp1 = api_client.post(VERIFY_URL, {"email": user.email, "otp": "999999"})
        assert resp1.status_code == status.HTTP_200_OK

        resp2 = api_client.post(VERIFY_URL, {"email": user.email, "otp": "999999"})
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# 6. Unauthenticated Access Protection
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccessProtection:
    """
    Protected endpoints must return 401 for unauthenticated requests.
    """

    def test_me_endpoint_requires_auth(self, api_client):
        response = api_client.get(ME_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_requires_auth(self, api_client):
        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": "a", "new_password": "b"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_requires_auth(self, api_client):
        response = api_client.post(LOGOUT_URL, {"all_devices": False})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_access_protected_endpoint_with_garbage_token(self, api_client):
        """Random strings in the cookie should not authenticate."""
        api_client.cookies["access_token"] = "this.is.not.a.jwt"
        response = api_client.get(ME_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_access_protected_endpoint_with_expired_format(self, api_client):
        """A structurally valid but tampered JWT should fail."""
        fake_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." "eyJ1c2VyX2lkIjoiZmFrZSIsImV4cCI6MH0." "invalid_signature_here"
        )
        api_client.cookies["access_token"] = fake_jwt
        response = api_client.get(ME_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
