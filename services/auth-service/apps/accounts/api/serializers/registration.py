import re

from rest_framework import serializers


def validate_password_strength(value):
    if not re.search(r"[a-z]", value):
        raise serializers.ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", value):
        raise serializers.ValidationError("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    return value


class CustomerRegisterInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate_full_name(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Full name cannot be blank.")
        return val


class VendorRegisterInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=255)
    business_email = serializers.EmailField()
    business_phone = serializers.CharField(max_length=20)
    preferred_domain = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate_full_name(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Full name cannot be blank.")
        return val

    def validate_business_name(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Business name cannot be blank.")
        return val
