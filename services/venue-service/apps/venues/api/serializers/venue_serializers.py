"""
Venue Serializers — Data validation and JSON representation.
"""

from rest_framework import serializers

from apps.venues.core.constants import PolicyType, PriceType
from apps.venues.core.models import Venue, VenueImage, VenuePolicy

from .amenity_serializers import AmenitySerializer
from .category_serializers import VenueCategorySerializer

# =============================================================================
# Read Serializers (Output)
# =============================================================================


class VenueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueImage
        fields = ("id", "image_url", "caption", "is_primary", "sort_order")


class VenuePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = VenuePolicy
        fields = ("id", "title", "content", "policy_type")


class VenueListSerializer(serializers.ModelSerializer):
    """Used for public search and list views. Lightweight."""

    category = VenueCategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = (
            "id",
            "name",
            "slug",
            "city",
            "state",
            "capacity",
            "base_price",
            "price_type",
            "category",
            "primary_image",
            "approval_status",
            "is_active",
        )

    def get_primary_image(self, obj):
        # We expect primary_image to be prefetched via to_attr in the selector
        if hasattr(obj, "primary_image") and obj.primary_image:
            return VenueImageSerializer(obj.primary_image[0]).data
        return None


class VenueDetailSerializer(serializers.ModelSerializer):
    """Used for public detail view. Includes everything."""

    category = VenueCategorySerializer(read_only=True)
    images = VenueImageSerializer(many=True, read_only=True)
    amenities = serializers.SerializerMethodField()
    policies = VenuePolicySerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        fields = (
            "id",
            "vendor_id",
            "tenant_id",
            "name",
            "slug",
            "description",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "capacity",
            "base_price",
            "price_type",
            "category",
            "images",
            "amenities",
            "policies",
            "approval_status",
            "is_active",
            "created_at",
        )

    def get_amenities(self, obj):
        # We expect venue_amenities__amenity to be prefetched
        amenities = [va.amenity for va in obj.venue_amenities.all()]
        return AmenitySerializer(amenities, many=True).data


# =============================================================================
# Write Serializers (Input)
# =============================================================================


class PolicyInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    policy_type = serializers.ChoiceField(choices=PolicyType.choices, default=PolicyType.GENERAL)


class VenueCreateInputSerializer(serializers.Serializer):
    """Validates input for creating a venue."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.UUIDField()
    address = serializers.CharField(max_length=500)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100, default="India")
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    capacity = serializers.IntegerField(min_value=1)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    price_type = serializers.ChoiceField(choices=PriceType.choices, default=PriceType.FULL_DAY)

    amenity_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    policies = PolicyInputSerializer(many=True, required=False)


class VenueUpdateInputSerializer(VenueCreateInputSerializer):
    """All fields are optional for update."""

    name = serializers.CharField(max_length=255, required=False)
    category_id = serializers.UUIDField(required=False)
    address = serializers.CharField(max_length=500, required=False)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    capacity = serializers.IntegerField(min_value=1, required=False)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)


# =============================================================================
# Image Serializers (Input)
# =============================================================================


class ImageRegistrationInputSerializer(serializers.Serializer):
    image_url = serializers.URLField()
    public_id = serializers.CharField(required=False, allow_blank=True)
    caption = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(default=False)
    sort_order = serializers.IntegerField(required=False)
