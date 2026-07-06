from rest_framework import serializers


class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenRefreshInputSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ValidateContextInputSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    tenant_id = serializers.UUIDField(required=False)


class LogoutInputSerializer(serializers.Serializer):
    all_devices = serializers.BooleanField(default=False)
