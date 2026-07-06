"""
Reusable DRF permission classes for the accounts domain.

Usage in views:
    permission_classes = [IsGlobalAdmin]
    permission_classes = [IsInternalService]
"""

from django.conf import settings
from rest_framework.permissions import BasePermission

from apps.accounts.core.constants import UserGlobalRole


class IsGlobalAdmin(BasePermission):
    """
    Grants access only to users with global_role == ADMIN.

    Use on platform-admin-only endpoints (approve venues, suspend tenants, etc.)
    """

    message = "You do not have platform admin privileges."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.global_role == UserGlobalRole.ADMIN)


class IsInternalService(BasePermission):
    """
    Validates that the caller is a trusted internal microservice.

    Checks the X-Internal-API-Key header against INTERNAL_SERVICE_API_KEY
    from settings. Replaces the manual header check previously scattered
    in each internal view.

    Usage:
        permission_classes = [IsInternalService]
    """

    message = "Invalid or missing X-Internal-API-Key header."

    def has_permission(self, request, view) -> bool:
        expected_key = getattr(settings, "INTERNAL_SERVICE_API_KEY", None)
        if not expected_key:
            # If the key is not configured, block all access
            return False
        incoming_key = request.headers.get("X-Internal-Api-Key")
        return bool(incoming_key and incoming_key == expected_key)
