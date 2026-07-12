from unittest.mock import MagicMock, patch

import pytest
from apps.tenants.core.models import ServiceRegistry, Tenant, TenantServiceProvision, TenantServiceProvisionStatus
from apps.tenants.tasks import dispatch_tenant_provisioning
from celery.exceptions import Retry

pytestmark = pytest.mark.django_db


class TestDispatchTenantProvisioningTask:
    @pytest.fixture
    def setup_data(self, verified_user):
        tenant = Tenant.objects.create(
            name="Test Venue", slug="test-venue", contact_email="test@venue.local", created_by=verified_user
        )
        service = ServiceRegistry.objects.create(
            name="venue-service",
            display_name="Venue Microservice",
            base_url="http://venue-service:8001",
            provision_endpoint="/internal/tenants/provision/",
        )
        provision = TenantServiceProvision.objects.create(
            tenant=tenant, service=service, status=TenantServiceProvisionStatus.PENDING
        )
        return provision, tenant, service

    @patch("apps.tenants.tasks.requests.post")
    def test_successful_provisioning_marks_created(self, mock_post, setup_data):
        provision, tenant, service = setup_data

        # Mock successful HTTP 201 response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        # Execute
        result = dispatch_tenant_provisioning(str(provision.id))

        # Verify
        assert result is True
        provision.refresh_from_db()
        assert provision.status == TenantServiceProvisionStatus.CREATED
        assert provision.provisioned_at is not None
        assert provision.error_message == ""

        mock_post.assert_called_once_with(
            "http://venue-service:8001/internal/tenants/provision/",
            json={
                "tenant_id": str(tenant.id),
                "name": "Test Venue",
                "slug": "test-venue",
                "contact_email": "test@venue.local",
                "contact_phone": "",
            },
            headers={"X-Internal-API-Key": "dev-internal-api-key", "Content-Type": "application/json"},
            timeout=15,
        )

    @patch("apps.tenants.tasks.requests.post")
    @patch("apps.tenants.tasks.dispatch_tenant_provisioning.retry")
    def test_http_error_triggers_retry(self, mock_retry, mock_post, setup_data):
        provision, _, _ = setup_data

        # Mock failing HTTP 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        mock_retry.side_effect = Retry("Retrying task...")

        # Execute
        with pytest.raises(Retry):
            dispatch_tenant_provisioning(str(provision.id))

        # Verify
        mock_post.assert_called_once()
        mock_retry.assert_called_once()

        provision.refresh_from_db()
        assert provision.status == TenantServiceProvisionStatus.PENDING

    @patch("apps.tenants.tasks.dispatch_tenant_provisioning.retry")
    def test_missing_base_url_marks_failed_immediately(self, mock_retry, setup_data):
        provision, _, service = setup_data

        # Remove base_url
        service.base_url = ""
        service.save()

        # Execute
        result = dispatch_tenant_provisioning(str(provision.id))

        # Verify
        assert result is None
        provision.refresh_from_db()
        assert provision.status == TenantServiceProvisionStatus.FAILED
        assert "No base_url configured" in provision.error_message
        mock_retry.assert_not_called()
