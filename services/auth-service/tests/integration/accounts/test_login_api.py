"""
Integration tests for the Login and Token Refresh API endpoints.

These tests hit actual HTTP endpoints through DRF's test client,
verifying the full request → serializer → service → response pipeline.
"""

import pytest
from apps.accounts.models import User
from rest_framework import status

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/refresh/"


# ---------------------------------------------------------------------------
# Login API
# ---------------------------------------------------------------------------


class TestLoginAPI:
    def test_login_success_returns_200(self, api_client, verified_user, user_password):
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["user"]["email"] == verified_user.email

    def test_login_sets_httponly_cookies(self, api_client, verified_user, user_password):
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        assert response.cookies["access_token"]["httponly"] is True
        assert response.cookies["refresh_token"]["httponly"] is True

    def test_login_returns_user_data(self, api_client, verified_user, user_password):
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        user_data = response.data["data"]["user"]
        assert user_data["email"] == verified_user.email
        assert user_data["full_name"] == verified_user.full_name
        assert user_data["global_role"] == verified_user.global_role

    def test_login_invalid_password_returns_401(self, api_client, verified_user):
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": "WrongPass1!"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_nonexistent_user_returns_401(self, api_client):
        response = api_client.post(LOGIN_URL, {"email": "ghost@test.com", "password": "Pass123!"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields_returns_400(self, api_client):
        response = api_client.post(LOGIN_URL, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_unverified_user_returns_403(self, api_client, user_password):
        user = User.objects.create_user(
            email="unverified@login.com",
            password=user_password,
            full_name="Unverified",
            is_verified=False,
        )
        response = api_client.post(LOGIN_URL, {"email": user.email, "password": user_password})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_login_inactive_user_returns_403(self, api_client, inactive_user, user_password):
        response = api_client.post(LOGIN_URL, {"email": inactive_user.email, "password": user_password})

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Token Refresh API
# ---------------------------------------------------------------------------


class TestTokenRefreshAPI:
    def test_refresh_with_valid_cookie_returns_200(self, api_client, verified_user, user_password):
        login_resp = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})
        assert login_resp.status_code == status.HTTP_200_OK

        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_refresh_without_cookie_returns_401(self, api_client):
        response = api_client.post(REFRESH_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_sets_new_access_cookie(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(REFRESH_URL)
        assert "access_token" in response.cookies
