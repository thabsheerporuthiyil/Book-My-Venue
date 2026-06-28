from django.contrib import admin

from .models import (
    ServiceRegistry,
    Tenant,
    TenantDomain,
    TenantMembership,
    TenantServiceProvision,
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "schema_name", "status", "contact_email", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug", "schema_name", "contact_email")


@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary", "created_at")
    search_fields = ("domain", "tenant__name")


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("tenant", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("tenant__name", "user__email")


@admin.register(ServiceRegistry)
class ServiceRegistryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "display_name",
        "base_url",
        "requires_tenant_provisioning",
        "is_active",
    )
    list_filter = ("requires_tenant_provisioning", "is_active")
    search_fields = ("name", "display_name", "base_url")


@admin.register(TenantServiceProvision)
class TenantServiceProvisionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "service", "schema_name", "status", "provisioned_at", "updated_at")
    list_filter = ("service", "status")
    search_fields = ("tenant__name", "service__name", "schema_name")