"""
Integration tests for the OTP verification and resend API endpoints.
"""

import pytest
from apps.accounts.core.services.otp import _get_otp_cache_key
from apps.accounts.models import User
from django.core.cache import cache
from rest_framework import status

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

VERIFY_URL = "/api/auth/verify-otp/"
RESEND_URL = "/api/auth/resend-otp/"


class TestVerifyOTPAPI:
    def test_valid_otp_returns_200(self, api_client, db, user_password):
        user = User.objects.create_user(
            email="otpverify@test.com",
            password=user_password,
            full_name="OTP Verify",
            is_verified=False,
        )
        cache_key = _get_otp_cache_key(user.email)
        cache.set(cache_key, "123456", timeout=300)

        response = api_client.post(VERIFY_URL, {"email": user.email, "otp": "123456"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_invalid_otp_returns_400(self, api_client, db, user_password):
        user = User.objects.create_user(
            email="otpbad@test.com",
            password=user_password,
            full_name="OTP Bad",
            is_verified=False,
        )
        cache_key = _get_otp_cache_key(user.email)
        cache.set(cache_key, "123456", timeout=300)

        response = api_client.post(VERIFY_URL, {"email": user.email, "otp": "000000"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_expired_otp_returns_400(self, api_client, verified_user):
        response = api_client.post(VERIFY_URL, {"email": verified_user.email, "otp": "123456"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_fields_returns_400(self, api_client):
        response = api_client.post(VERIFY_URL, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestResendOTPAPI:
    def test_resend_for_unverified_user_returns_200(self, api_client, db, user_password, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        User.objects.create_user(
            email="resend@test.com",
            password=user_password,
            full_name="Resend User",
            is_verified=False,
        )

        response = api_client.post(RESEND_URL, {"email": "resend@test.com"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_resend_for_already_verified_returns_200(self, api_client, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")

        response = api_client.post(RESEND_URL, {"email": verified_user.email})

        assert response.status_code == status.HTTP_200_OK

    def test_resend_for_nonexistent_email_returns_200(self, api_client, db):
        """Returns 200 even for unknown emails to prevent email enumeration."""
        response = api_client.post(RESEND_URL, {"email": "nonexistent@test.com"})

        assert response.status_code == status.HTTP_200_OK
