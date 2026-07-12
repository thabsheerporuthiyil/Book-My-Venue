import pytest
from apps.venues.core.models import VenueCategory
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_category():
    return VenueCategory.objects.create(name="Test Category")


@pytest.fixture
def api_client():
    return APIClient()


class TestVenueCreateAPI:
    def test_create_venue_success(self, api_client, test_category, mock_auth_service):
        """
        Tests the full HTTP flow, including:
        - Cross-service JWT authentication mock
        - Serializer validation
        - Service layer execution
        - Response formatting
        """

        # Set the mock JWT cookie
        api_client.cookies["access_token"] = "fake-jwt-token"

        payload = {
            "name": "Grand Hall",
            "category_id": str(test_category.id),
            "address": "456 Event Rd",
            "city": "Mumbai",
            "state": "MH",
            "capacity": 1000,
            "base_price": "50000.00",
        }

        response = api_client.post("/api/venues/my-venues/create/", data=payload, format="json")

        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Grand Hall"
        assert data["approval_status"] == "PENDING_APPROVAL"

        # Assert the mock tenant UUID was properly associated
        assert data["tenant_id"] == "22222222-2222-2222-2222-222222222222"
        assert data["vendor_id"] == "11111111-1111-1111-1111-111111111111"

    def test_create_venue_unauthenticated(self, api_client, test_category):
        """Test that missing JWT cookie results in 401 Unauthorized."""

        payload = {
            "name": "Grand Hall",
            "category_id": str(test_category.id),
            "address": "456 Event Rd",
            "city": "Mumbai",
            "state": "MH",
            "capacity": 1000,
            "base_price": "50000.00",
        }

        response = api_client.post("/api/venues/my-venues/create/", data=payload, format="json")

        assert response.status_code == 401
