from rest_framework import serializers

from apps.venues.core.models import VenueCategory


class VenueCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueCategory
        fields = ("id", "name", "slug", "description")
