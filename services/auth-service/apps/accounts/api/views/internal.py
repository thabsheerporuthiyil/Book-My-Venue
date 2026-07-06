from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.api.serializers.auth import ValidateContextInputSerializer
from apps.accounts.core.permissions import IsInternalService
from apps.accounts.core.selectors.users import get_active_user_by_id
from apps.tenants.core.models import TenantStatus
from apps.tenants.core.selectors.memberships import get_user_membership


class ValidateContextInternalAPIView(APIView):
    permission_classes = [IsInternalService]

    @extend_schema(request=ValidateContextInputSerializer)
    def post(self, request):
        serializer = ValidateContextInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data["access_token"]
        tenant_id = serializer.validated_data.get("tenant_id")

        try:
            token = AccessToken(access_token)
            user_id = token.get("user_id")
        except (TokenError, InvalidToken):
            return Response(
                {"valid": False, "message": "Invalid or expired token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = get_active_user_by_id(user_id)
        if not user:
            return Response(
                {"valid": False, "message": "User not found or inactive."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tenant_data = {"id": None, "role": ""}

        if tenant_id:
            membership = get_user_membership(user, tenant_id)
            if not membership or membership.tenant.status != TenantStatus.ACTIVE:
                return Response(
                    {"valid": False, "message": "User lacks tenant access."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            tenant_data = {
                "id": membership.tenant.id,
                "role": membership.role,
            }

        return Response(
            {
                "valid": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "global_role": user.global_role,
                },
                "tenant": tenant_data,
            },
            status=status.HTTP_200_OK,
        )
