import uuid

from django.conf import settings
from django.db import models


class TenantStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    REJECTED = "REJECTED", "Rejected"


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    schema_name = models.SlugField(unique=True)

    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.PENDING,
    )

    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tenants",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TenantDomain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="domains",
    )

    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.domain


class TenantMembershipRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"


class TenantMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=TenantMembershipRole.choices,
        default=TenantMembershipRole.OWNER,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "user")

    def __str__(self):
        return f"{self.user} - {self.tenant} - {self.role}"


class ServiceRegistry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=150)

    base_url = models.URLField(blank=True)

    requires_tenant_provisioning = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    provision_endpoint = models.CharField(
        max_length=255,
        default="/internal/tenants/provision/",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TenantServiceProvisionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CREATED = "CREATED", "Created"
    FAILED = "FAILED", "Failed"


class TenantServiceProvision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="service_provisions",
    )

    service = models.ForeignKey(
        ServiceRegistry,
        on_delete=models.PROTECT,
        related_name="tenant_provisions",
    )

    schema_name = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=TenantServiceProvisionStatus.choices,
        default=TenantServiceProvisionStatus.PENDING,
    )

    error_message = models.TextField(blank=True)

    provisioned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "service")

    def __str__(self):
        return f"{self.tenant.name} - {self.service.name} - {self.status}"