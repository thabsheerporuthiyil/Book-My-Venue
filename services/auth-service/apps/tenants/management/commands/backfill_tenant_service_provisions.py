from django.core.management.base import BaseCommand

from apps.tenants.models import (
    ServiceRegistry,
    Tenant,
    TenantServiceProvision,
)


class Command(BaseCommand):
    help = "Create missing TenantServiceProvision records for existing tenants."

    def handle(self, *args, **options):
        services = ServiceRegistry.objects.filter(
            is_active=True,
            requires_tenant_provisioning=True,
        )

        tenants = Tenant.objects.all()

        created_count = 0

        for tenant in tenants:
            for service in services:
                _, created = TenantServiceProvision.objects.get_or_create(
                    tenant=tenant,
                    service=service,
                    defaults={
                        "schema_name": tenant.schema_name,
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created provision: {tenant.name} -> {service.name}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill completed. Created {created_count} provision records."
            )
        )