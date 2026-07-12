from django.urls import path

from apps.venues.api.views.approval_views import (
    PendingVenueListAPIView,
    VenueApproveAPIView,
    VenueRejectAPIView,
    VenueSuspendAPIView,
)
from apps.venues.api.views.category_views import AmenityListAPIView, CategoryListAPIView
from apps.venues.api.views.vendor_venue_views import (
    VendorVenueDetailAPIView,
    VendorVenueListAPIView,
    VenueImageDeleteAPIView,
    VenueImageRegisterAPIView,
    VenueImageUploadParamsAPIView,
)
from apps.venues.api.views.venue_views import (
    VenueCreateAPIView,
    VenueDetailAPIView,
    VenueListAPIView,
)

urlpatterns = [
    # -------------------------------------------------------------------------
    # Public Search & Listing (No Auth Required)
    # -------------------------------------------------------------------------
    path("", VenueListAPIView.as_view(), name="venue-list"),
    path("<uuid:venue_id>/", VenueDetailAPIView.as_view(), name="venue-detail"),
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("amenities/", AmenityListAPIView.as_view(), name="amenity-list"),
    # -------------------------------------------------------------------------
    # Vendor Endpoints (Auth: TenantOwnerOrManager)
    # -------------------------------------------------------------------------
    path("my-venues/", VendorVenueListAPIView.as_view(), name="vendor-venue-list"),
    path("my-venues/create/", VenueCreateAPIView.as_view(), name="venue-create"),
    path("my-venues/<uuid:venue_id>/", VendorVenueDetailAPIView.as_view(), name="vendor-venue-detail"),
    # Image Upload Flow (Client-side directly to Cloudinary)
    path(
        "my-venues/<uuid:venue_id>/images/upload-params/",
        VenueImageUploadParamsAPIView.as_view(),
        name="venue-image-upload-params",
    ),
    path(
        "my-venues/<uuid:venue_id>/images/register/",
        VenueImageRegisterAPIView.as_view(),
        name="venue-image-register",
    ),
    path(
        "my-venues/<uuid:venue_id>/images/<uuid:image_id>/",
        VenueImageDeleteAPIView.as_view(),
        name="venue-image-delete",
    ),
    # -------------------------------------------------------------------------
    # Admin Endpoints (Auth: PlatformAdmin)
    # -------------------------------------------------------------------------
    path("admin/pending/", PendingVenueListAPIView.as_view(), name="admin-pending-venues"),
    path("admin/<uuid:venue_id>/approve/", VenueApproveAPIView.as_view(), name="admin-venue-approve"),
    path("admin/<uuid:venue_id>/reject/", VenueRejectAPIView.as_view(), name="admin-venue-reject"),
    path("admin/<uuid:venue_id>/suspend/", VenueSuspendAPIView.as_view(), name="admin-venue-suspend"),
]
