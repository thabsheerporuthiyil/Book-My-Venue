from django.core.management.base import BaseCommand

from apps.tenants.models import ServiceRegistry


class Command(BaseCommand):
    help = "Seed default microservices into ServiceRegistry."

    def handle(self, *args, **options):
        services = [
            {
                "name": "venue-service",
                "display_name": "Venue Service",
                "base_url": "http://venue-service:8002",
                "requires_tenant_provisioning": True,
                "is_active": True,
            },
            {
                "name": "booking-service",
                "display_name": "Booking Service",
                "base_url": "http://booking-service:8003",
                "requires_tenant_provisioning": True,
                "is_active": True,
            },
            {
                "name": "notification-service",
                "display_name": "Notification Service",
                "base_url": "http://notification-service:8004",
                "requires_tenant_provisioning": True,
                "is_active": True,
            },
            {
                "name": "ai-service",
                "display_name": "AI Service",
                "base_url": "http://ai-service:8005",
                "requires_tenant_provisioning": False,
                "is_active": True,
            },
        ]

        for service_data in services:
            service, created = ServiceRegistry.objects.update_or_create(
                name=service_data["name"],
                defaults=service_data,
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created service: {service.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated service: {service.name}"))