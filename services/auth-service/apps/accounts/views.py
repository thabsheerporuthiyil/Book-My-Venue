from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from drf_spectacular.utils import extend_schema, inline_serializer

from apps.tenants.models import TenantMembership, TenantStatus

from .serializers import (
    CustomerRegisterSerializer,
    LoginSerializer,
    MeResponseSerializer,
    TokenRefreshSerializer,
    ValidateContextSerializer,
    VendorRegisterSerializer,
)

User = get_user_model()


class CustomerRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=CustomerRegisterSerializer,
        responses={
            201: inline_serializer(
                name="CustomerRegisterResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "data": inline_serializer(
                        name="CustomerRegisterData",
                        fields={
                            "user_id": serializers.UUIDField(),
                            "email": serializers.EmailField(),
                            "global_role": serializers.CharField(),
                        },
                    ),
                },
            )
        },
    )
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Customer registered successfully.",
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

    @extend_schema(
        request=VendorRegisterSerializer,
        responses={
            201: inline_serializer(
                name="VendorRegisterResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "data": inline_serializer(
                        name="VendorRegisterData",
                        fields={
                            "user_id": serializers.UUIDField(),
                            "email": serializers.EmailField(),
                            "tenant_id": serializers.UUIDField(),
                            "tenant_name": serializers.CharField(),
                            "schema_name": serializers.CharField(),
                            "domain": serializers.CharField(),
                            "status": serializers.CharField(),
                        },
                    ),
                },
            )
        },
    )
    def post(self, request):
        serializer = VendorRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tenant = serializer.save()

        primary_domain = tenant.domains.filter(is_primary=True).first()

        return Response(
            {
                "success": True,
                "message": "Vendor registered successfully. Tenant is waiting for approval.",
                "data": {
                    "user_id": user.id,
                    "email": user.email,
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "schema_name": tenant.schema_name,
                    "domain": primary_domain.domain if primary_domain else "",
                    "status": tenant.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "data": inline_serializer(
                        name="LoginData",
                        fields={
                            "access": serializers.CharField(),
                            "refresh": serializers.CharField(),
                            "user": inline_serializer(
                                name="LoginUserData",
                                fields={
                                    "id": serializers.UUIDField(),
                                    "email": serializers.EmailField(),
                                    "full_name": serializers.CharField(),
                                    "global_role": serializers.CharField(),
                                },
                            ),
                        },
                    ),
                },
            )
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
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


class TokenRefreshAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=TokenRefreshSerializer,
        responses={
            200: inline_serializer(
                name="TokenRefreshResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "data": inline_serializer(
                        name="TokenRefreshData",
                        fields={
                            "access": serializers.CharField(),
                        },
                    ),
                },
            )
        },
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
        except TokenError:
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token.",
                    "errors": {
                        "refresh": "Invalid or expired refresh token."
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "success": True,
                "message": "Token refreshed successfully.",
                "data": {
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="MeResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "data": MeResponseSerializer(),
                },
            )
        },
    )
    def get(self, request):
        user = request.user

        return Response(
            {
                "success": True,
                "message": "User fetched successfully.",
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "global_role": user.global_role,
                    "is_verified": user.is_verified,
                },
            },
            status=status.HTTP_200_OK,
        )


class ValidateContextInternalAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=ValidateContextSerializer,
        responses={
            200: inline_serializer(
                name="ValidateContextResponse",
                fields={
                    "valid": serializers.BooleanField(),
                    "user": inline_serializer(
                        name="ValidateContextUser",
                        fields={
                            "id": serializers.UUIDField(),
                            "email": serializers.EmailField(),
                            "global_role": serializers.CharField(),
                        },
                    ),
                    "tenant": inline_serializer(
                        name="ValidateContextTenant",
                        fields={
                            "id": serializers.UUIDField(allow_null=True),
                            "schema_name": serializers.CharField(allow_blank=True),
                            "role": serializers.CharField(allow_blank=True),
                        },
                    ),
                },
            )
        },
    )
    def post(self, request):
        internal_key = request.headers.get("X-Internal-API-Key")
        expected_key = getattr(settings, "INTERNAL_SERVICE_API_KEY", None)

        if expected_key and internal_key != expected_key:
            return Response(
                {
                    "valid": False,
                    "message": "Invalid internal API key.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = ValidateContextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data["access_token"]
        tenant_id = serializer.validated_data.get("tenant_id")

        try:
            token = AccessToken(access_token)
            user_id = token.get("user_id")
            user = User.objects.get(id=user_id, is_active=True)
        except Exception:
            return Response(
                {
                    "valid": False,
                    "message": "Invalid token.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tenant_data = {
            "id": None,
            "schema_name": "",
            "role": "",
        }

        if tenant_id:
            membership = (
                TenantMembership.objects.select_related("tenant")
                .filter(
                    user=user,
                    tenant_id=tenant_id,
                    is_active=True,
                    tenant__status=TenantStatus.ACTIVE,
                )
                .first()
            )

            if not membership:
                return Response(
                    {
                        "valid": False,
                        "message": "User does not have access to this tenant.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            tenant_data = {
                "id": membership.tenant.id,
                "schema_name": membership.tenant.schema_name,
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