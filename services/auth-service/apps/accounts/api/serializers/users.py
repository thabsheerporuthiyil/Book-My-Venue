from rest_framework import serializers


class MeResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    global_role = serializers.CharField()
    is_verified = serializers.BooleanField()
