from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from apps.accounts.core.exceptions import (
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from apps.accounts.core.models import CustomerProfile
from apps.tenants.core.models import TenantDomain
from apps.tenants.core.services import create_vendor_with_tenant

User = get_user_model()


@transaction.atomic
def register_customer(email, full_name, password, phone=""):
    email = email.lower().strip()
    if User.objects.filter(email=email).exists():
        raise UserAlreadyExistsError("User with this email already exists.")

    user = User.objects.create_user(email=email, password=password, full_name=full_name, phone=phone)
    CustomerProfile.objects.create(user=user)
    return user


def register_vendor_orchestrator(
    email,
    full_name,
    password,
    business_name,
    business_email,
    business_phone,
    phone="",
    preferred_domain="",
):
    email = email.lower().strip()
    if User.objects.filter(email=email).exists():
        raise UserAlreadyExistsError("User with this email already exists.")

    tenant_slug = slugify(business_name.strip())
    if not tenant_slug:
        raise ValueError("Invalid business name.")

    domain_prefix = slugify(preferred_domain.strip()) if preferred_domain else tenant_slug
    domain = f"{domain_prefix}.bookmyvenue.local"

    if TenantDomain.objects.filter(domain=domain).exists():
        raise DomainAlreadyTakenError("This domain is already taken.")

    vendor_data = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "phone": phone,
        "business_name": business_name,
        "business_email": business_email,
        "business_phone": business_phone,
        "tenant_slug": tenant_slug,
        "domain": domain,
    }
    return create_vendor_with_tenant(vendor_data)
