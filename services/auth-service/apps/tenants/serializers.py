from rest_framework import serializers

from .models import TenantMembership


class MyTenantMembershipSerializer(
    serializers.ModelSerializer
):
    tenant_id = serializers.UUIDField(
        source="tenant.id",
        read_only=True,
    )

    name = serializers.CharField(
        source="tenant.name",
        read_only=True,
    )

    slug = serializers.CharField(
        source="tenant.slug",
        read_only=True,
    )

    schema_name = serializers.CharField(
        source="tenant.schema_name",
        read_only=True,
    )

    status = serializers.CharField(
        source="tenant.status",
        read_only=True,
    )

    class Meta:
        model = TenantMembership
        fields = [
            "tenant_id",
            "name",
            "slug",
            "schema_name",
            "status",
            "role",
            "is_active",
        ]