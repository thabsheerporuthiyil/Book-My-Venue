"""
Integration tests for the Customer Registration API endpoint.

Verifies the full HTTP request pipeline including serializer validation,
service layer orchestration, and response contract.
"""

import pytest
from apps.accounts.core.models import CustomerProfile
from apps.accounts.models import User
from rest_framework import status

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

REGISTER_URL = "/api/auth/register/customer/"

VALID_PAYLOAD = {
    "email": "newcustomer@test.com",
    "full_name": "New Customer",
    "password": "StrongPass123!",
    "phone": "9876543210",
}


class TestCustomerRegistrationAPI:
    def test_register_success_returns_201(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["email"] == VALID_PAYLOAD["email"]

    def test_creates_user_in_database(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        api_client.post(REGISTER_URL, VALID_PAYLOAD)

        assert User.objects.filter(email=VALID_PAYLOAD["email"]).exists()

    def test_creates_customer_profile(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        api_client.post(REGISTER_URL, VALID_PAYLOAD)

        user = User.objects.get(email=VALID_PAYLOAD["email"])
        assert CustomerProfile.objects.filter(user=user).exists()

    def test_user_starts_unverified(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        api_client.post(REGISTER_URL, VALID_PAYLOAD)

        user = User.objects.get(email=VALID_PAYLOAD["email"])
        assert user.is_verified is False

    def test_triggers_otp_celery_task(self, api_client, mocker):
        mock_delay = mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        api_client.post(REGISTER_URL, VALID_PAYLOAD)

        mock_delay.assert_called_once()

    def test_duplicate_email_returns_409(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        api_client.post(REGISTER_URL, VALID_PAYLOAD)
        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_weak_password_returns_400(self, api_client):
        payload = {**VALID_PAYLOAD, "password": "weak"}
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email_returns_400(self, api_client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "email"}
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_full_name_returns_400(self, api_client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "full_name"}
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_without_uppercase_returns_400(self, api_client):
        payload = {**VALID_PAYLOAD, "password": "weakpass123!"}
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_without_special_char_returns_400(self, api_client):
        payload = {**VALID_PAYLOAD, "password": "WeakPass123"}
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
