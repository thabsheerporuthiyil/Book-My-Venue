import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.fixture
def clean_cache():
    cache.clear()
    yield
    cache.clear()


class TestTokenRefreshAPI:
    def test_token_refresh_caches_response_for_concurrent_requests(
        self, api_client, verified_user, user_password, clean_cache
    ):
        # 1. Login to get initial tokens
        login_url = reverse("login")
        login_data = {"email": verified_user.email, "password": user_password}
        login_response = api_client.post(login_url, login_data, format="json")

        assert login_response.status_code == status.HTTP_200_OK
        refresh_token = login_response.cookies.get("refresh_token").value

        # 2. First refresh request
        refresh_url = reverse("token-refresh")
        api_client.cookies["refresh_token"] = refresh_token

        first_refresh = api_client.post(refresh_url)
        assert first_refresh.status_code == status.HTTP_200_OK

        first_new_access = first_refresh.cookies.get("access_token").value
        first_new_refresh = first_refresh.cookies.get("refresh_token").value

        # 3. Simulate concurrent second refresh request with the EXACT SAME old refresh token
        # Normally this fails with 401 because the first request rotated and blacklisted it.
        # But our Redis caching fix should instantly return the cached new tokens.
        api_client.cookies["refresh_token"] = refresh_token
        second_refresh = api_client.post(refresh_url)

        assert second_refresh.status_code == status.HTTP_200_OK
        assert second_refresh.data["message"] == "Token refreshed (cached)."

        second_new_access = second_refresh.cookies.get("access_token").value
        second_new_refresh = second_refresh.cookies.get("refresh_token").value

        # Verify the tokens returned are identical to the first request's newly generated tokens
        assert first_new_access == second_new_access
        assert first_new_refresh == second_new_refresh
