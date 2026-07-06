from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.api.serializers.otp import (
    ResendOTPInputSerializer,
    VerifyOTPInputSerializer,
)
from apps.accounts.core.services.otp import generate_and_send_otp, verify_otp
from apps.accounts.models import User


class VerifyOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(request=VerifyOTPInputSerializer)
    def post(self, request):
        serializer = VerifyOTPInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["otp"]

        is_valid = verify_otp(email, code)

        if not is_valid:
            return Response(
                {"success": False, "message": "Invalid or expired OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )


class ResendOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(request=ResendOTPInputSerializer)
    def post(self, request):
        serializer = ResendOTPInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email.strip().lower())

            if user.is_verified:
                return Response(
                    {"success": False, "message": "Account is already verified."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            generate_and_send_otp(user)

        except User.DoesNotExist:
            # Silently succeed to prevent email enumeration attacks
            pass

        return Response(
            {
                "success": True,
                "message": "If the account exists and is unverified, an OTP has been sent.",
            },
            status=status.HTTP_200_OK,
        )
