"""Category Selectors."""

from apps.venues.core.models import VenueCategory


def list_active_categories():
    """List all active platform categories."""
    return VenueCategory.objects.filter(is_active=True).order_by("name")
