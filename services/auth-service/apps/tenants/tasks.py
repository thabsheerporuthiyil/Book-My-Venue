import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name="tenants.dispatch_tenant_provisioning",
    bind=True,
    max_retries=5,
    default_retry_delay=60,  # Start with 60 seconds, exponentially back off
)
def dispatch_tenant_provisioning(self, provision_id: str):
    """
    Celery task that acts as the distributed transaction orchestrator.
    It takes a pending TenantServiceProvision record and makes a secure HTTP
    call to the downstream microservice to provision the tenant database schema.
    """
    from apps.tenants.core.models import TenantServiceProvision, TenantServiceProvisionStatus

    try:
        provision = TenantServiceProvision.objects.select_related("tenant", "service").get(id=provision_id)
    except TenantServiceProvision.DoesNotExist:
        logger.error(f"TenantServiceProvision {provision_id} not found.")
        return

    if provision.status == TenantServiceProvisionStatus.CREATED:
        logger.info(f"Provision {provision_id} is already CREATED. Skipping.")
        return

    service = provision.service
    tenant = provision.tenant

    if not service.base_url:
        logger.error(f"Service {service.name} has no base_url configured.")
        provision.status = TenantServiceProvisionStatus.FAILED
        provision.error_message = "No base_url configured for service."
        provision.save(update_fields=["status", "error_message", "updated_at"])
        return

    target_url = f"{service.base_url.rstrip('/')}{service.provision_endpoint}"

    headers = {
        "X-Internal-API-Key": getattr(settings, "INTERNAL_SERVICE_API_KEY", ""),
        "Content-Type": "application/json",
    }

    payload = {
        "tenant_id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "contact_email": tenant.contact_email,
        "contact_phone": tenant.contact_phone,
    }

    try:
        logger.info(f"Dispatching provision request to {service.name} at {target_url}")

        # Timeout of 15 seconds to prevent hanging Celery workers
        response = requests.post(target_url, json=payload, headers=headers, timeout=15)

        if response.status_code in [200, 201]:
            logger.info(f"Successfully provisioned tenant {tenant.slug} in {service.name}")
            provision.status = TenantServiceProvisionStatus.CREATED
            provision.provisioned_at = timezone.now()
            provision.error_message = ""
            provision.save(update_fields=["status", "provisioned_at", "error_message", "updated_at"])
            return True
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.warning(f"Provisioning failed for {tenant.slug} in {service.name}: {error_msg}")

            # Retry with exponential backoff (e.g. 60s, 120s, 240s)
            countdown = self.default_retry_delay * (2**self.request.retries)
            raise self.retry(exc=Exception(error_msg), countdown=countdown)

    except requests.RequestException as e:
        error_msg = f"Network/Timeout Error: {str(e)}"
        logger.warning(f"Provisioning network error for {tenant.slug} in {service.name}: {error_msg}")

        countdown = self.default_retry_delay * (2**self.request.retries)
        try:
            raise self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for {provision_id}. Marking as FAILED.")
            provision.status = TenantServiceProvisionStatus.FAILED
            provision.error_message = f"Max retries exceeded: {error_msg}"
            provision.save(update_fields=["status", "error_message", "updated_at"])
            return False
