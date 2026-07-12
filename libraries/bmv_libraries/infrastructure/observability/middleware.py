import uuid

import structlog
from django.utils.deprecation import MiddlewareMixin

logger = structlog.get_logger(__name__)


class CorrelationIDMiddleware(MiddlewareMixin):
    """
    Middleware that ensures every request has a Correlation ID.
    If 'X-Correlation-ID' is passed by the Gateway, it uses it.
    Otherwise, it generates a new UUID.

    It binds the correlation_id to structlog context variables so that
    all subsequent logs for this request include it.
    It also adds it to the HTTP response header.
    """

    def process_request(self, request):
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.correlation_id = correlation_id
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    def process_response(self, request, response):
        if hasattr(request, "correlation_id"):
            response["X-Correlation-ID"] = request.correlation_id

        # Clear contextvars for the next request in the thread
        structlog.contextvars.clear_contextvars()
        return response
