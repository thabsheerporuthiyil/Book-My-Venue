"""
Integration tests for the Logout API endpoint.
"""

import pytest
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

LOGOUT_URL = "/api/auth/logout/"
LOGIN_URL = "/api/auth/login/"


class TestLogoutAPI:
    def test_logout_returns_200(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(LOGOUT_URL, {"all_devices": False})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_logout_clears_cookies(self, api_client, verified_user, user_password):
        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(LOGOUT_URL, {"all_devices": False})

        access_cookie = response.cookies.get("access_token")
        assert access_cookie is not None
        assert access_cookie["max-age"] == 0

    def test_logout_all_devices_blacklists_tokens(self, api_client, verified_user, user_password):
        RefreshToken.for_user(verified_user)
        RefreshToken.for_user(verified_user)

        api_client.post(LOGIN_URL, {"email": verified_user.email, "password": user_password})

        response = api_client.post(LOGOUT_URL, {"all_devices": True})

        assert response.status_code == status.HTTP_200_OK
        blacklisted = BlacklistedToken.objects.filter(token__user=verified_user).count()
        assert blacklisted >= 3

    def test_logout_requires_authentication(self, api_client):
        response = api_client.post(LOGOUT_URL, {"all_devices": False})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
