from apps.accounts.api.views.auth import LoginAPIView, TokenRefreshAPIView
from apps.accounts.api.views.logout import LogoutAPIView
from apps.accounts.api.views.otp import ResendOTPAPIView, VerifyOTPAPIView
from apps.accounts.api.views.password import (
    ChangePasswordAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
)
from apps.accounts.api.views.registration import (
    CustomerRegisterAPIView,
    VendorRegisterAPIView,
)
from apps.accounts.api.views.users import MeAPIView
from django.urls import path

urlpatterns = [
    path(
        "register/customer/",
        CustomerRegisterAPIView.as_view(),
        name="register-customer",
    ),
    path("register/vendor/", VendorRegisterAPIView.as_view(), name="register-vendor"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path("resend-otp/", ResendOTPAPIView.as_view(), name="resend-otp"),
    path("me/", MeAPIView.as_view(), name="me"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
]
