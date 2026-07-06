import logging

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers.registration import (
    CustomerRegisterInputSerializer,
    VendorRegisterInputSerializer,
)
from apps.accounts.core.services.otp import generate_and_send_otp
from apps.accounts.core.services.registration import (
    register_customer,
    register_vendor_orchestrator,
)

logger = logging.getLogger(__name__)


class CustomerRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=CustomerRegisterInputSerializer)
    def post(self, request):
        serializer = CustomerRegisterInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Step 1: Register user (may raise UserAlreadyExistsError → handled by global handler)
        user = register_customer(**serializer.validated_data)

        # Step 2: Send OTP (best-effort — if Redis is down, registration still succeeds)
        try:
            generate_and_send_otp(user)
        except Exception:
            logger.exception("Failed to send OTP for user %s during registration", user.email)

        return Response(
            {
                "success": True,
                "message": "Customer registered successfully. Please check your email for the OTP.",
                "data": {
                    "user_id": user.id,
                    "email": user.email,
                    "global_role": user.global_role,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class VendorRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=VendorRegisterInputSerializer)
    def post(self, request):
        serializer = VendorRegisterInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Step 1: Register vendor + tenant (may raise business exceptions → handled by global handler)
        user, tenant = register_vendor_orchestrator(**serializer.validated_data)

        # Step 2: Send OTP (best-effort — if Redis is down, registration still succeeds)
        try:
            generate_and_send_otp(user)
        except Exception:
            logger.exception("Failed to send OTP for vendor %s during registration", user.email)

        primary_domain = tenant.domains.filter(is_primary=True).first()
        return Response(
            {
                "success": True,
                "message": (
                    "Vendor registered successfully. "
                    "Please check your email for the OTP. Tenant is waiting for approval."
                ),
                "data": {
                    "user_id": user.id,
                    "email": user.email,
                    "tenant_id": tenant.id,
                    "domain": primary_domain.domain if primary_domain else "",
                    "status": tenant.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )
