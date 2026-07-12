from apps.tenants.api.views.memberships import MyTenantsAPIView
from django.urls import path

urlpatterns = [
    path("me/tenants/", MyTenantsAPIView.as_view(), name="my-tenants"),
]
