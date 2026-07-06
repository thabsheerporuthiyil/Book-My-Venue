from django.urls import path

from apps.tenants.api.views.memberships import MyTenantsAPIView

urlpatterns = [
    path("me/tenants/", MyTenantsAPIView.as_view(), name="my-tenants"),
]
