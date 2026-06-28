from django.urls import path

from .views import (
    CustomerRegisterAPIView,
    LoginAPIView,
    MeAPIView,
    TokenRefreshAPIView,
    VendorRegisterAPIView,
)

urlpatterns = [
    path("register/customer/", CustomerRegisterAPIView.as_view(), name="register-customer"),
    path("register/vendor/", VendorRegisterAPIView.as_view(), name="register-vendor"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
]