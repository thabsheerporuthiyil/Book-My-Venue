from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsInternalService
from apps.venues.core.constants import ApprovalStatus
from apps.venues.core.models import Venue


class InternalVenueValidationAPIView(APIView):
    """
    Called by the Booking Service to validate that a venue exists,
    is active, and is approved before allowing a booking to proceed.
    """

    permission_classes = [IsInternalService]
    authentication_classes = []  # Bypass JWT validation for internal service-to-service calls

    @extend_schema(responses={200: dict, 404: dict})
    def get(self, request, venue_id):
        try:
            venue = Venue.objects.get(id=venue_id, is_active=True, approval_status=ApprovalStatus.APPROVED)
            return Response(
                {
                    "valid": True,
                    "venue_id": venue.id,
                    "tenant_id": venue.tenant_id,
                    "vendor_id": venue.vendor_id,
                    "base_price": venue.base_price,
                    "capacity": venue.capacity,
                    "name": venue.name,
                }
            )
        except Venue.DoesNotExist:
            return Response(
                {"valid": False, "message": "Venue not found or not approved."}, status=status.HTTP_404_NOT_FOUND
            )
