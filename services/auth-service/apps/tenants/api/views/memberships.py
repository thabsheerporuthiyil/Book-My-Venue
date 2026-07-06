from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.api.serializers.memberships import MyTenantMembershipSerializer
from apps.tenants.core.selectors import get_user_tenant_memberships


class MyTenantsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MyTenantMembershipSerializer(many=True)})
    def get(self, request):
        memberships = get_user_tenant_memberships(request.user)
        serializer = MyTenantMembershipSerializer(memberships, many=True)
        return Response(
            {
                "success": True,
                "message": "Tenants fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
