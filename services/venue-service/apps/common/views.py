from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response({"status": "ok", "service": "venue-service"}, status=status.HTTP_200_OK)


class DeepHealthCheckView(APIView):
    """
    Verifies that all critical backend dependencies (PostgreSQL, Redis) are reachable.
    Used for Readiness Probes in Kubernetes and external uptime monitoring.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: dict, 503: dict})
    def get(self, request):
        dependencies = {
            "database": "unknown",
            "redis_cache": "unknown",
        }
        is_healthy = True

        # 1. Check PostgreSQL
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    dependencies["database"] = "ok"
                else:
                    dependencies["database"] = "error"
                    is_healthy = False
        except Exception:
            dependencies["database"] = "unreachable"
            is_healthy = False

        # 2. Check Redis (Cache)
        try:
            from django.core.cache import cache

            cache.set("health_check_ping", "pong", timeout=5)
            if cache.get("health_check_ping") == "pong":
                dependencies["redis_cache"] = "ok"
            else:
                dependencies["redis_cache"] = "error"
                is_healthy = False
        except Exception:
            dependencies["redis_cache"] = "unreachable"
            is_healthy = False

        status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(
            {
                "status": "ok" if is_healthy else "degraded",
                "service": "venue-service",
                "dependencies": dependencies,
            },
            status=status_code,
        )
