from apps.common.views import DeepHealthCheckView, HealthCheckView
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("health/deep/", DeepHealthCheckView.as_view(), name="deep-health-check"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/", include("apps.accounts.api.urls.public")),
    path("api/auth/", include("apps.tenants.api.urls.public")),
    path("internal/", include("apps.accounts.api.urls.internal")),
]


# Conditionally inject Dev-Only routes
if settings.DEBUG:
    urlpatterns += [
        path("silk/", include("silk.urls", namespace="silk")),
    ]
