from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers.password import ChangePasswordInputSerializer
from apps.accounts.api.utils import delete_jwt_cookies
from apps.accounts.core.services.auth import change_user_password


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ChangePasswordInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = ChangePasswordInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # InvalidCredentialsError and SamePasswordError bubble up to the
        # global exception handler with their respective error_code/status_code.
        change_user_password(
            user=request.user,
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
        )

        response = Response(
            {
                "success": True,
                "message": "Password changed successfully. Please log in again.",
            },
            status=status.HTTP_200_OK,
        )
        # Clear cookies since all sessions were just blacklisted
        return delete_jwt_cookies(response)
