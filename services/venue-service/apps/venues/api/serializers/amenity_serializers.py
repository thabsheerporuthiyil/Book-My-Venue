from rest_framework import serializers

from apps.venues.core.models import Amenity


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name", "slug", "icon")
