from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.api.serializers.auth import LogoutInputSerializer
from apps.accounts.api.utils import delete_jwt_cookies
from apps.accounts.core.services.auth import logout_all_user_sessions


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=LogoutInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = LogoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        all_devices = serializer.validated_data.get("all_devices", False)
        # Extract refresh token from cookies instead of request body
        refresh_token = request.COOKIES.get(getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh_token"))

        if all_devices:
            logout_all_user_sessions(request.user)
            response = Response(
                {
                    "success": True,
                    "message": "Successfully logged out from all devices.",
                },
                status=status.HTTP_200_OK,
            )
            return delete_jwt_cookies(response)

        if not refresh_token:
            response = Response(
                {
                    "success": False,
                    "message": "Refresh token is required unless all_devices is true.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            return delete_jwt_cookies(response)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

        response = Response(
            {"success": True, "message": "Logout successful."},
            status=status.HTTP_200_OK,
        )
        return delete_jwt_cookies(response)
