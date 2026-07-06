from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers.users import MeResponseSerializer


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MeResponseSerializer})
    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "User fetched successfully.",
                "data": MeResponseSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )
