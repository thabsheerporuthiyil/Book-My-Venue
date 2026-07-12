"""Amenity Selectors."""

from apps.venues.core.models import Amenity


def list_active_amenities():
    """List all active platform amenities."""
    return Amenity.objects.filter(is_active=True).order_by("name")
