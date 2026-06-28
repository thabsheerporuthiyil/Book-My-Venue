from django.urls import path

from .views import MyTenantsAPIView

urlpatterns = [
    path("me/tenants/", MyTenantsAPIView.as_view(), name="my-tenants"),
]