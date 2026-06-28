from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.models import CustomerProfile
from apps.tenants.models import (
    ServiceRegistry,
    Tenant,
    TenantDomain,
    TenantMembership,
    TenantMembershipRole,
    TenantServiceProvision,
)

User = get_user_model()


class CustomerRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            phone=validated_data.get("phone", ""),
        )

        CustomerProfile.objects.create(user=user)

        return user


class VendorRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    business_name = serializers.CharField(max_length=255)
    business_email = serializers.EmailField()
    business_phone = serializers.CharField(max_length=20)
    preferred_domain = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")

        return value

    def validate_business_name(self, value):
        value = value.strip()
        slug = slugify(value)

        if not slug:
            raise serializers.ValidationError("Business name is invalid.")

        if Tenant.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                "Tenant with this business name already exists."
            )

        return value

    def validate_preferred_domain(self, value):
        if not value:
            return ""

        domain_prefix = slugify(value.strip())

        if not domain_prefix:
            raise serializers.ValidationError("Preferred domain is invalid.")

        return domain_prefix

    def validate(self, attrs):
        business_name = attrs.get("business_name")
        preferred_domain = attrs.get("preferred_domain", "")

        tenant_slug = slugify(business_name)

        domain_prefix = preferred_domain if preferred_domain else tenant_slug
        domain = f"{domain_prefix}.bookmyvenue.local"

        if TenantDomain.objects.filter(domain=domain).exists():
            raise serializers.ValidationError({
                "preferred_domain": "This domain is already taken."
            })

        attrs["tenant_slug"] = tenant_slug
        attrs["domain_prefix"] = domain_prefix
        attrs["domain"] = domain

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        tenant_slug = validated_data["tenant_slug"]
        domain = validated_data["domain"]

        business_name = validated_data["business_name"]

        schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            phone=validated_data.get("phone", ""),
        )

        tenant = Tenant.objects.create(
            name=business_name,
            slug=tenant_slug,
            schema_name=schema_name,
            contact_email=validated_data["business_email"],
            contact_phone=validated_data["business_phone"],
            created_by=user,
        )

        TenantMembership.objects.create(
            tenant=tenant,
            user=user,
            role=TenantMembershipRole.OWNER,
        )

        TenantDomain.objects.create(
            tenant=tenant,
            domain=domain,
            is_primary=True,
        )

        active_services = ServiceRegistry.objects.filter(
            is_active=True,
            requires_tenant_provisioning=True,
        )

        provisions = [
            TenantServiceProvision(
                tenant=tenant,
                service=service,
                schema_name=schema_name,
            )
            for service in active_services
        ]

        TenantServiceProvision.objects.bulk_create(provisions)

        return user, tenant


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()

        user = authenticate(
            username=email,
            password=attrs["password"],
        )

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        attrs["user"] = user
        return attrs


class MeResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    global_role = serializers.CharField()
    is_verified = serializers.BooleanField()


class ValidateContextSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    tenant_id = serializers.UUIDField(required=False)

class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()