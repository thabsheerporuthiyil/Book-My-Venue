from django.urls import path

from apps.venues.api.views.internal_views import InternalVenueValidationAPIView

urlpatterns = [
    # Used by Booking Service to ensure venue exists and is approved before booking
    path(
        "venues/<uuid:venue_id>/booking-validation/",
        InternalVenueValidationAPIView.as_view(),
        name="internal-venue-validation",
    ),
]
