"""
Venue Selectors — Read-only database queries.

Selectors encapsulate complex queries, prefetching, and filtering logic.
Views should call selectors instead of using Venue.objects directly.
"""

from django.db.models import Prefetch

from apps.venues.core.constants import ApprovalStatus
from apps.venues.core.exceptions import VenueNotFoundError
from apps.venues.core.models import Venue, VenueImage


def get_venue_by_id(*, venue_id):
    """
    Get a single venue with all its relations prefetched.
    Used for public detail views. Only returns APPROVED venues.
    """
    try:
        return Venue.objects.prefetch_related(
            "category",
            "policies",
            "venue_amenities__amenity",
            Prefetch("images", queryset=VenueImage.objects.all().order_by("sort_order")),
        ).get(id=venue_id, is_active=True, approval_status=ApprovalStatus.APPROVED)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e


def list_approved_venues(queryset=None):
    """
    Base queryset for public venue searches.
    Prefetches only what is needed for a list view (e.g., primary image).
    """
    qs = queryset or Venue.objects.all()

    primary_image_qs = VenueImage.objects.filter(is_primary=True)

    return (
        qs.filter(is_active=True, approval_status=ApprovalStatus.APPROVED)
        .select_related("category")
        .prefetch_related(Prefetch("images", queryset=primary_image_qs, to_attr="primary_image"))
        .order_by("-created_at")
    )


def list_vendor_venues(*, vendor_id, tenant_id):
    """
    List all venues owned by a specific vendor/tenant.
    Includes all approval statuses. Used in the vendor dashboard.
    """
    primary_image_qs = VenueImage.objects.filter(is_primary=True)

    return (
        Venue.objects.filter(vendor_id=vendor_id, tenant_id=tenant_id, is_active=True)
        .select_related("category")
        .prefetch_related(Prefetch("images", queryset=primary_image_qs, to_attr="primary_image"))
        .order_by("-created_at")
    )


def list_pending_venues():
    """Admin only: List venues awaiting approval."""
    return (
        Venue.objects.filter(approval_status=ApprovalStatus.PENDING_APPROVAL, is_active=True)
        .select_related("category")
        .order_by("created_at")
    )
