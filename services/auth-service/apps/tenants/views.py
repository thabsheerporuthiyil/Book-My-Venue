from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer

from .models import TenantMembership
from .serializers import MyTenantMembershipSerializer


class MyTenantsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="MyTenantsResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "data": MyTenantMembershipSerializer(many=True),
                },
            )
        },
    )
    def get(self, request):
        memberships = (
            TenantMembership.objects.select_related("tenant")
            .filter(user=request.user, is_active=True)
            .order_by("-created_at")
        )

        serializer = MyTenantMembershipSerializer(memberships, many=True)

        return Response(
            {
                "success": True,
                "message": "Tenants fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )