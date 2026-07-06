from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from apps.accounts.api.serializers.auth import (
    LoginInputSerializer,
    TokenRefreshInputSerializer,
)
from apps.accounts.api.throttles import LoginRateThrottle
from apps.accounts.api.utils import set_jwt_cookies
from apps.accounts.core.services.auth import authenticate_user, get_tokens_for_user


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(request=LoginInputSerializer)
    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # All business exceptions (AccountLockedError, InvalidCredentialsError,
        # InactiveUserError, UnverifiedAccountError) now bubble up to the
        # global exception handler which maps them to the correct HTTP status
        # and returns a consistent JSON envelope with error_code.
        user = authenticate_user(**serializer.validated_data)

        tokens = get_tokens_for_user(user)
        response = Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "global_role": user.global_role,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
        set_jwt_cookies(response, tokens["access"], tokens.get("refresh"))
        return response


class TokenRefreshAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=TokenRefreshInputSerializer, responses={200: dict})
    def post(self, request):
        # We need to extract the refresh token from the cookie instead of the request body
        refresh_token = request.COOKIES.get(getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh_token"))

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "error_code": "INVALID_TOKEN",
                    "message": "No refresh token provided in cookies.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # We pass the refresh token into the serializer's data dictionary to simulate a normal request
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {
                    "success": False,
                    "error_code": "INVALID_TOKEN",
                    "message": "Invalid or expired refresh token.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response(
            {
                "success": True,
                "message": "Token refreshed.",
            },
            status=status.HTTP_200_OK,
        )

        tokens = serializer.validated_data
        set_jwt_cookies(response, tokens["access"], tokens.get("refresh"))
        return response
