from apps.tenants.core.models import TenantMembership


def get_user_tenant_memberships(user):
    return TenantMembership.objects.select_related("tenant").filter(user=user, is_active=True).order_by("-created_at")


def get_user_membership(user, tenant_id):
    return (
        TenantMembership.objects.select_related("tenant").filter(user=user, tenant_id=tenant_id, is_active=True).first()
    )
