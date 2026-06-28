from .models import (
    ServiceRegistry,
    Tenant,
    TenantMembership,
)


def get_active_provision_services():
    return ServiceRegistry.objects.filter(
        is_active=True,
        requires_tenant_provisioning=True,
    )


def get_user_tenant_memberships(user):
    return (
        TenantMembership.objects
        .select_related("tenant")
        .filter(
            user=user,
            is_active=True,
        )
        .order_by("-created_at")
    )


def get_tenant_by_id(tenant_id):
    return (
        Tenant.objects
        .filter(id=tenant_id)
        .first()
    )


def get_user_membership(
    user,
    tenant_id,
):
    return (
        TenantMembership.objects
        .select_related("tenant")
        .filter(
            user=user,
            tenant_id=tenant_id,
            is_active=True,
        )
        .first()
    )