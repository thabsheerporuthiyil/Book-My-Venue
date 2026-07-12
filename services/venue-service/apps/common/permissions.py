"""
DRF Permission classes for the Venue Service.

These permissions rely on the AuthenticatedUser object injected by
InternalJWTAuthentication. They check:
  - Tenant membership role (OWNER, MANAGER, STAFF)
  - Platform-wide global role (ADMIN)
"""

from rest_framework.permissions import BasePermission


class IsTenantMember(BasePermission):
    """Allows access if the user has any role in the tenant specified by X-Tenant-Id."""

    message = "You must be a member of this tenant."

    def has_permission(self, request, view):
        user = request.user
        return (
            hasattr(user, "is_authenticated")
            and user.is_authenticated
            and hasattr(user, "tenant")
            and user.tenant is not None
        )


class IsTenantOwnerOrManager(BasePermission):
    """Allows access only if the user's tenant role is OWNER or MANAGER."""

    message = "Only venue owners or managers can perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not (hasattr(user, "is_authenticated") and user.is_authenticated):
            return False
        if not hasattr(user, "tenant") or user.tenant is None:
            return False
        return user.tenant.role in ("OWNER", "MANAGER")


class IsPlatformAdmin(BasePermission):
    """Allows access only if the user's global_role is ADMIN."""

    message = "Only platform administrators can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return (
            hasattr(user, "is_authenticated")
            and user.is_authenticated
            and getattr(user, "global_role", None) == "ADMIN"
        )


class IsInternalService(BasePermission):
    """Allows access only if the request carries a valid X-Internal-API-Key header."""

    message = "Access forbidden."

    def has_permission(self, request, view):
        from django.conf import settings

        api_key = request.headers.get("X-Internal-API-Key")
        return api_key == settings.INTERNAL_SERVICE_API_KEY
