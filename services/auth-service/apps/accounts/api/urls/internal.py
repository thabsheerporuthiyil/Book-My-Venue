from django.urls import path

from apps.accounts.api.views.internal import ValidateContextInternalAPIView

urlpatterns = [
    path(
        "auth/validate-context/",
        ValidateContextInternalAPIView.as_view(),
        name="validate-context",
    ),
]
