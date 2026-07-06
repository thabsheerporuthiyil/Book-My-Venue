from rest_framework import serializers


class VerifyOTPInputSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)


class ResendOTPInputSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
