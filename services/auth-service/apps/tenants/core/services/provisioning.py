from django.contrib.auth import get_user_model
from django.db import transaction

from apps.tenants.core.models import (
    Tenant,
    TenantDomain,
    TenantMembership,
    TenantMembershipRole,
    TenantServiceProvision,
)
from apps.tenants.core.selectors import get_active_provision_services

User = get_user_model()


@transaction.atomic
def create_vendor_with_tenant(validated_data):
    tenant_slug = validated_data["tenant_slug"]
    business_name = validated_data["business_name"]
    domain = validated_data["domain"]

    user = User.objects.create_user(
        email=validated_data["email"],
        password=validated_data["password"],
        full_name=validated_data["full_name"],
        phone=validated_data.get("phone", ""),
    )

    tenant = Tenant.objects.create(
        name=business_name,
        slug=tenant_slug,
        contact_email=validated_data["business_email"],
        contact_phone=validated_data["business_phone"],
        created_by=user,
    )

    TenantMembership.objects.create(tenant=tenant, user=user, role=TenantMembershipRole.OWNER)
    TenantDomain.objects.create(tenant=tenant, domain=domain, is_primary=True)

    services = get_active_provision_services()
    provisions = [TenantServiceProvision(tenant=tenant, service=service) for service in services]
    TenantServiceProvision.objects.bulk_create(provisions)

    return user, tenant
