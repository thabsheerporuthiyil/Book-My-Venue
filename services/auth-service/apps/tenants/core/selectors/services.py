from apps.tenants.core.models import ServiceRegistry


def get_active_provision_services():
    return ServiceRegistry.objects.filter(is_active=True, requires_tenant_provisioning=True)
