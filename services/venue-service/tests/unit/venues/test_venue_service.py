import uuid

import pytest
from apps.venues.core.constants import ApprovalStatus
from apps.venues.core.exceptions import CategoryNotFoundError, DuplicateVenueSlugError
from apps.venues.core.models import VenueCategory
from apps.venues.core.services.venue_service import create_venue

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_category():
    return VenueCategory.objects.create(name="Test Category")


class TestVenueService:
    def test_create_venue_success(self, test_category):
        vendor_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        data = {
            "name": "My Awesome Venue",
            "category_id": test_category.id,
            "address": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "capacity": 500,
            "base_price": "1000.00",
        }

        venue = create_venue(vendor_id=vendor_id, tenant_id=tenant_id, data=data)

        assert venue.id is not None
        assert venue.name == "My Awesome Venue"
        assert venue.slug == "my-awesome-venue"
        assert venue.vendor_id == vendor_id
        assert venue.tenant_id == tenant_id
        assert venue.approval_status == ApprovalStatus.PENDING_APPROVAL

    def test_create_venue_duplicate_slug_raises_error(self, test_category):
        vendor_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        data = {
            "name": "My Awesome Venue",
            "category_id": test_category.id,
            "address": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "capacity": 500,
            "base_price": "1000.00",
        }

        # First creation succeeds
        create_venue(vendor_id=vendor_id, tenant_id=tenant_id, data=data)

        # Second creation with same name (same slug) in same tenant should fail
        with pytest.raises(DuplicateVenueSlugError):
            create_venue(vendor_id=vendor_id, tenant_id=tenant_id, data=data)

    def test_create_venue_invalid_category_raises_error(self):
        vendor_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        data = {
            "name": "My Awesome Venue",
            "category_id": uuid.uuid4(),  # Random UUID that doesn't exist
            "address": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "capacity": 500,
            "base_price": "1000.00",
        }

        with pytest.raises(CategoryNotFoundError):
            create_venue(vendor_id=vendor_id, tenant_id=tenant_id, data=data)
