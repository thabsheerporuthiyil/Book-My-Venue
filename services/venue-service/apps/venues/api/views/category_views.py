from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.venues.api.serializers.amenity_serializers import AmenitySerializer
from apps.venues.api.serializers.category_serializers import VenueCategorySerializer
from apps.venues.core.selectors.amenity_selector import list_active_amenities
from apps.venues.core.selectors.category_selector import list_active_categories


class CategoryListAPIView(APIView):
    """Public endpoint to list active venue categories."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=VenueCategorySerializer(many=True))
    def get(self, request):
        categories = list_active_categories()
        serializer = VenueCategorySerializer(categories, many=True)
        return Response(serializer.data)


class AmenityListAPIView(APIView):
    """Public endpoint to list active venue amenities."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=AmenitySerializer(many=True))
    def get(self, request):
        amenities = list_active_amenities()
        serializer = AmenitySerializer(amenities, many=True)
        return Response(serializer.data)
