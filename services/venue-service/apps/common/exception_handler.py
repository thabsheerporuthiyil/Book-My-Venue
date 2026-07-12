"""
Global DRF Exception Handler for the Venue Service.

Ensures EVERY error response returns a consistent JSON envelope:
    {
        "success": false,
        "error_code": "VALIDATION_ERROR",
        "message": "Invalid input.",
        "errors": {"name": ["This field is required."]}
    }
"""

import logging
import traceback
import uuid

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Intercepts all exceptions raised during DRF request processing.

    Priority order:
        1. VenueBaseException subclasses (business logic).
        2. DRF's built-in exceptions (validation, auth, throttling).
        3. Unhandled / unexpected exceptions (500 safety net).
    """
    from apps.venues.core.exceptions import VenueBaseException

    # 1. Custom Business Logic Exceptions
    if isinstance(exc, VenueBaseException):
        logger.warning(
            "Business logic error: %s | %s",
            exc.error_code,
            exc.message,
        )
        return _build_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
        )

    # 2. DRF Built-in Exceptions
    response = drf_exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            return _build_error_response(
                error_code="VALIDATION_ERROR",
                message="Invalid input.",
                status_code=response.status_code,
                errors=response.data,
            )

        if isinstance(exc, NotAuthenticated | AuthenticationFailed):
            message = _extract_detail(
                response.data,
                "Authentication credentials were not provided or are invalid.",
            )
            return _build_error_response(
                error_code="AUTHENTICATION_FAILED",
                message=message,
                status_code=response.status_code,
            )

        if isinstance(exc, PermissionDenied):
            message = _extract_detail(response.data, "You do not have permission to perform this action.")
            return _build_error_response(
                error_code="PERMISSION_DENIED",
                message=message,
                status_code=response.status_code,
            )

        if isinstance(exc, Throttled):
            wait = exc.wait
            message = f"Request throttled. Try again in {int(wait)} seconds." if wait else "Too many requests."
            return _build_error_response(
                error_code="THROTTLED",
                message=message,
                status_code=response.status_code,
            )

        if isinstance(exc, APIException):
            message = _extract_detail(response.data, "An error occurred.")
            return _build_error_response(
                error_code="API_ERROR",
                message=message,
                status_code=response.status_code,
            )

        return response

    # 3. Unhandled / Unexpected Exception (500 Safety Net)
    request_id = str(uuid.uuid4())
    logger.error(
        "Unhandled exception [request_id=%s]: %s\n%s",
        request_id,
        str(exc),
        traceback.format_exc(),
    )

    return _build_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


# =============================================================================
# Helpers
# =============================================================================


def _build_error_response(error_code, message, status_code, errors=None, request_id=None):
    """Constructs the standardized error response envelope."""
    from rest_framework.response import Response

    body = {
        "success": False,
        "error_code": error_code,
        "message": message,
    }
    if errors:
        body["errors"] = errors
    if request_id:
        body["request_id"] = request_id

    return Response(body, status=status_code)


def _extract_detail(data, default):
    """Extracts a human-readable message from DRF's response data."""
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
    if isinstance(data, list) and data:
        return str(data[0])
    if isinstance(data, str):
        return data
    return default
