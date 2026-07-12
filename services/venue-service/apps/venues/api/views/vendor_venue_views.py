from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsTenantOwnerOrManager
from apps.venues.api.serializers.venue_serializers import (
    ImageRegistrationInputSerializer,
    VenueDetailSerializer,
    VenueImageSerializer,
    VenueListSerializer,
    VenueUpdateInputSerializer,
)
from apps.venues.core.selectors.venue_selector import get_venue_by_id, list_vendor_venues
from apps.venues.core.services.venue_service import (
    delete_venue_image,
    generate_image_upload_params,
    register_uploaded_image,
    update_venue,
)


class VendorVenueListAPIView(APIView):
    """List all venues belonging to the current vendor's tenant."""

    permission_classes = [IsTenantOwnerOrManager]

    @extend_schema(responses=VenueListSerializer(many=True))
    def get(self, request):
        venues = list_vendor_venues(
            vendor_id=request.user.id,
            tenant_id=request.user.tenant.id,
        )
        serializer = VenueListSerializer(venues, many=True)
        return Response(serializer.data)


class VendorVenueDetailAPIView(APIView):
    """Update a specific venue belonging to the vendor."""

    permission_classes = [IsTenantOwnerOrManager]

    @extend_schema(request=VenueUpdateInputSerializer, responses={200: VenueDetailSerializer})
    def patch(self, request, venue_id):
        serializer = VenueUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_venue(
            venue_id=venue_id,
            tenant_id=request.user.tenant.id,
            vendor_id=request.user.id,
            data=serializer.validated_data,
        )

        venue = get_venue_by_id(venue_id=venue_id, require_approved=False)
        return Response(VenueDetailSerializer(venue).data)


class VenueImageUploadParamsAPIView(APIView):
    """
    Get signed parameters to upload an image directly to Cloudinary/S3
    from the frontend browser.
    """

    permission_classes = [IsTenantOwnerOrManager]

    @extend_schema(responses={200: dict})
    def get(self, request, venue_id):
        params = generate_image_upload_params(
            venue_id=venue_id,
            tenant_id=request.user.tenant.id,
            vendor_id=request.user.id,
        )
        return Response(params)


class VenueImageRegisterAPIView(APIView):
    """
    Register an image that was successfully uploaded by the frontend.
    """

    permission_classes = [IsTenantOwnerOrManager]

    @extend_schema(request=ImageRegistrationInputSerializer, responses={201: VenueImageSerializer})
    def post(self, request, venue_id):
        serializer = ImageRegistrationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = register_uploaded_image(
            venue_id=venue_id,
            tenant_id=request.user.tenant.id,
            vendor_id=request.user.id,
            data=serializer.validated_data,
        )

        return Response(VenueImageSerializer(image).data, status=status.HTTP_201_CREATED)


class VenueImageDeleteAPIView(APIView):
    """Delete a venue image."""

    permission_classes = [IsTenantOwnerOrManager]

    @extend_schema(responses={204: None})
    def delete(self, request, venue_id, image_id):
        delete_venue_image(
            image_id=image_id,
            venue_id=venue_id,
            tenant_id=request.user.tenant.id,
            vendor_id=request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
