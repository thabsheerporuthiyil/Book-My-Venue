from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformAdmin
from apps.venues.api.serializers.venue_serializers import VenueDetailSerializer
from apps.venues.core.selectors.venue_selector import list_pending_venues
from apps.venues.core.services.approval_service import approve_venue, reject_venue, suspend_venue


class PendingVenueListAPIView(APIView):
    """Admin only: List venues awaiting approval."""

    permission_classes = [IsPlatformAdmin]

    @extend_schema(responses=VenueDetailSerializer(many=True))
    def get(self, request):
        venues = list_pending_venues()
        # For admin view, we might want a specific serializer, but detail is fine for now
        serializer = VenueDetailSerializer(venues, many=True)
        return Response(serializer.data)


class VenueApproveAPIView(APIView):
    """Admin only: Approve a venue."""

    permission_classes = [IsPlatformAdmin]

    @extend_schema(responses={200: dict})
    def post(self, request, venue_id):
        approve_venue(venue_id=venue_id)
        return Response({"status": "approved", "venue_id": venue_id})


class VenueRejectAPIView(APIView):
    """Admin only: Reject a venue."""

    permission_classes = [IsPlatformAdmin]

    @extend_schema(responses={200: dict})
    def post(self, request, venue_id):
        reason = request.data.get("reason")
        reject_venue(venue_id=venue_id, reason=reason)
        return Response({"status": "rejected", "venue_id": venue_id})


class VenueSuspendAPIView(APIView):
    """Admin only: Suspend an active venue."""

    permission_classes = [IsPlatformAdmin]

    @extend_schema(responses={200: dict})
    def post(self, request, venue_id):
        reason = request.data.get("reason")
        suspend_venue(venue_id=venue_id, reason=reason)
        return Response({"status": "suspended", "venue_id": venue_id})
