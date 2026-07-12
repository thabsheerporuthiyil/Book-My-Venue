from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsTenantOwnerOrManager
from apps.venues.api.serializers.venue_serializers import (
    VenueCreateInputSerializer,
    VenueDetailSerializer,
    VenueListSerializer,
)
from apps.venues.core.selectors.venue_selector import get_venue_by_id, list_approved_venues
from apps.venues.core.services.venue_service import create_venue


class VenueFilter(filters.FilterSet):
    city = filters.CharFilter(lookup_expr="iexact")
    category = filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    min_price = filters.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="base_price", lookup_expr="lte")
    min_capacity = filters.NumberFilter(field_name="capacity", lookup_expr="gte")


class VenueListAPIView(APIView):
    """
    Public endpoint to search and list approved venues.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=VenueListSerializer(many=True))
    def get(self, request):
        qs = list_approved_venues()

        # Apply filters manually for APIView (or use ListAPIView)
        filterset = VenueFilter(request.GET, queryset=qs)
        if filterset.is_valid():
            qs = filterset.qs

        # Pagination would normally go here, simplified for brevity
        # In a real app we'd use ListAPIView or manually apply pagination class
        serializer = VenueListSerializer(qs[:50], many=True)
        return Response(serializer.data)


class VenueDetailAPIView(APIView):
    """
    Public endpoint to get venue details by ID.
    Only returns approved venues.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=VenueDetailSerializer)
    def get(self, request, venue_id):
        venue = get_venue_by_id(venue_id=venue_id)
        serializer = VenueDetailSerializer(venue)
        return Response(serializer.data)


class VenueCreateAPIView(APIView):
    """
    Create a new venue under the vendor's tenant.
    """

    permission_classes = [IsTenantOwnerOrManager]

    @extend_schema(request=VenueCreateInputSerializer, responses={201: VenueDetailSerializer})
    def post(self, request):
        serializer = VenueCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        venue = create_venue(
            vendor_id=request.user.id,
            tenant_id=request.user.tenant.id,
            data=serializer.validated_data,
        )

        # Re-fetch with all relations for the response
        venue_with_relations = get_venue_by_id(venue_id=venue.id, require_approved=False)
        response_serializer = VenueDetailSerializer(venue_with_relations)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
