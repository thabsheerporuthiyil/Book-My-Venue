from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers.password import (
    ChangePasswordInputSerializer,
    ForgotPasswordInputSerializer,
    ResetPasswordInputSerializer,
)
from apps.accounts.api.throttles import ResendOTPRateThrottle
from apps.accounts.api.utils import delete_jwt_cookies
from apps.accounts.core.services.auth import change_user_password
from apps.accounts.core.services.password import (
    complete_password_reset,
    initiate_forgot_password,
)


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


class ForgotPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ResendOTPRateThrottle]  # Reuse 3/min limit

    @extend_schema(request=ForgotPasswordInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = ForgotPasswordInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        initiate_forgot_password(email=serializer.validated_data["email"])

        return Response(
            {
                "success": True,
                "message": "If the account exists, a password reset email has been sent.",
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ResendOTPRateThrottle]

    @extend_schema(request=ResetPasswordInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = ResetPasswordInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        complete_password_reset(
            email=serializer.validated_data["email"],
            otp=serializer.validated_data["otp"],
            new_password=serializer.validated_data["new_password"],
        )

        return Response(
            {
                "success": True,
                "message": "Password successfully reset. Please log in with your new password.",
            },
            status=status.HTTP_200_OK,
        )
