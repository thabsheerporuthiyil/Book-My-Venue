from apps.accounts.api.views.internal import ValidateContextInternalAPIView
from django.urls import path

urlpatterns = [
    path(
        "auth/validate-context/",
        ValidateContextInternalAPIView.as_view(),
        name="validate-context",
    ),
]
