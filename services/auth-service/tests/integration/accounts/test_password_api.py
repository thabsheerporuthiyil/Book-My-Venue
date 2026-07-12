"""
Integration tests for the Change Password API endpoint.
"""

import pytest
from rest_framework import status

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

LOGIN_URL = "/api/auth/login/"
CHANGE_PASSWORD_URL = "/api/auth/change-password/"


class TestChangePasswordAPI:
    def test_change_password_returns_200(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": user_password, "new_password": "NewSecure456!"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_change_password_clears_cookies(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": user_password, "new_password": "NewSecure456!"},
        )

        access_cookie = response.cookies.get("access_token")
        assert access_cookie is not None
        assert access_cookie["max-age"] == 0

    def test_wrong_current_password_returns_401(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": "WrongPass!", "new_password": "NewSecure456!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_same_password_returns_400(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": user_password, "new_password": user_password},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_requires_authentication(self, api_client, user_password):
        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": user_password, "new_password": "NewSecure456!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_can_login_with_new_password(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        new_password = "BrandNewPass789!"
        api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": user_password, "new_password": new_password},
        )

        api_client.cookies.clear()
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": new_password})

        assert response.status_code == status.HTTP_200_OK


class TestForgotPasswordAPI:
    from unittest.mock import patch

    @patch("apps.accounts.core.services.password.send_password_reset_email_task.delay")
    def test_forgot_password_sends_email_for_valid_user(self, mock_delay, api_client, verified_user):
        url = "/api/auth/forgot-password/"
        data = {"email": verified_user.email}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify cache has OTP
        from django.core.cache import cache

        cache_key = f"password_reset_otp:{verified_user.email}"
        assert cache.get(cache_key) is not None
        mock_delay.assert_called_once()

    @patch("apps.accounts.core.services.password.send_password_reset_email_task.delay")
    def test_forgot_password_returns_200_for_invalid_email_but_does_nothing(self, mock_delay, api_client):
        # Email Enumeration Prevention test
        url = "/api/auth/forgot-password/"
        data = {"email": "unknown@example.com"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        from django.core.cache import cache

        cache_key = "password_reset_otp:unknown@example.com"
        assert cache.get(cache_key) is None
        mock_delay.assert_not_called()


class TestResetPasswordAPI:
    def test_reset_password_success(self, api_client, verified_user):
        from django.core.cache import cache

        # 1. Setup OTP
        otp_code = "123456"
        cache_key = f"password_reset_otp:{verified_user.email}"
        cache.set(cache_key, otp_code, timeout=900)

        # 2. Call Reset API
        url = "/api/auth/reset-password/"
        data = {"email": verified_user.email, "otp": otp_code, "new_password": "NewStrongPassword123!"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify password actually changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("NewStrongPassword123!")

        # Verify cache cleared
        assert cache.get(cache_key) is None

    def test_reset_password_fails_with_invalid_otp(self, api_client, verified_user):
        url = "/api/auth/reset-password/"
        data = {"email": verified_user.email, "otp": "000000", "new_password": "NewStrongPassword123!"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error_code"] == "INVALID_OTP"
