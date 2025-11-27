"""Request ID middleware for request tracing."""

import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from my_api.infrastructure.logging import clear_request_id, set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request ID to all requests for tracing.

    Generates a unique request ID for each request or uses the one
    provided in X-Request-ID header. The ID is added to request state,
    logging context, and included in the response headers.
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Add request ID to request and response.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler in chain.

        Returns:
            Response with X-Request-ID header.
        """
        # Get existing request ID or generate new one
        request_id = request.headers.get(self.HEADER_NAME)
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Set request ID in logging context
        set_request_id(request_id)

        try:
            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[self.HEADER_NAME] = request_id

            return response
        finally:
            # Clear request ID from context
            clear_request_id()


def get_request_id(request: Request) -> str | None:
    """Get request ID from request state.

    Args:
        request: Current request.

    Returns:
        Request ID if available, None otherwise.
    """
    return getattr(request.state, "request_id", None)
