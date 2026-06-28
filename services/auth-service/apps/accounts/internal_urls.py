from django.urls import path

from .views import ValidateContextInternalAPIView

urlpatterns = [
    path("auth/validate-context/", ValidateContextInternalAPIView.as_view(), name="validate-context"),
]