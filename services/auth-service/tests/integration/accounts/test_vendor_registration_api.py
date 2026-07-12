"""
Integration tests for the Vendor Registration API endpoint.

Verifies the full HTTP request pipeline including tenant creation
and Celery task dispatching for orchestrating microservices.
"""

import pytest
from apps.accounts.models import User
from apps.tenants.core.models import (
    Tenant,
    TenantMembership,
    TenantServiceProvision,
)
from rest_framework import status

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

REGISTER_URL = "/api/auth/register/vendor/"

VALID_PAYLOAD = {
    "email": "newvendor@test.com",
    "full_name": "New Vendor",
    "password": "StrongPass123!",
    "phone": "9876543210",
    "business_name": "New Vendor Events",
    "business_email": "hello@newvendor.local",
    "business_phone": "1234567890",
    "preferred_domain": "newvendor",
}


class TestVendorRegistrationAPI:
    def test_register_success_returns_201(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        # Mock the dispatch task so it doesn't try to make real HTTP requests during testing
        mocker.patch("apps.tenants.core.services.provisioning.dispatch_tenant_provisioning.delay")

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_creates_user_and_tenant_in_database(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        mocker.patch("apps.tenants.core.services.provisioning.dispatch_tenant_provisioning.delay")

        api_client.post(REGISTER_URL, VALID_PAYLOAD)

        # 1. User created
        user = User.objects.get(email=VALID_PAYLOAD["email"])
        assert not user.is_verified

        # 2. Tenant created
        tenant = Tenant.objects.get(contact_email=VALID_PAYLOAD["business_email"])
        assert tenant.name == VALID_PAYLOAD["business_name"]

        # 3. Membership assigned
        membership = TenantMembership.objects.get(tenant=tenant, user=user)
        assert membership.role == "OWNER"

    def test_triggers_provisioning_celery_task(self, api_client, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")

        # We must mock the celery delay on the task
        mock_dispatch = mocker.patch("apps.tenants.core.services.provisioning.dispatch_tenant_provisioning.delay")

        # Mock transaction.on_commit to execute the callback immediately
        mocker.patch("django.db.transaction.on_commit", side_effect=lambda f: f())

        # Create dummy ServiceRegistry so we have something to provision
        from apps.tenants.core.models import ServiceRegistry

        ServiceRegistry.objects.create(
            name="venue-service",
            display_name="Venue Service",
            base_url="http://venue-service",
            provision_endpoint="/internal/provision",
        )

        api_client.post(REGISTER_URL, VALID_PAYLOAD)

        # Assert provision records were created in DB
        tenant = Tenant.objects.get(name=VALID_PAYLOAD["business_name"])
        provisions = TenantServiceProvision.objects.filter(tenant=tenant)
        assert provisions.count() == 1

        # Assert the celery task was dispatched
        mock_dispatch.assert_called_once_with(str(provisions.first().id))
