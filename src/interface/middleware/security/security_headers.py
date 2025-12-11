"""Security headers middleware for FastAPI.

**Feature: api-architecture-analysis**
**Validates: Requirements 5.3 (Security Headers)**
"""

from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to all responses.

    Implements standard security headers to protect against common
    web vulnerabilities like XSS, clickjacking, and MIME sniffing.
    """

    def __init__(
        self,
        app,
        *,
        content_security_policy: str | None = None,
        x_frame_options: str = "DENY",
        x_content_type_options: str = "nosniff",
        x_xss_protection: str = "1; mode=block",
        strict_transport_security: str = "max-age=31536000; includeSubDomains",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str | None = None,
    ) -> None:
        """Initialize security headers middleware.

        Args:
            app: ASGI application.
            content_security_policy: CSP header value (optional).
            x_frame_options: X-Frame-Options header value.
            x_content_type_options: X-Content-Type-Options header value.
            x_xss_protection: X-XSS-Protection header value.
            strict_transport_security: HSTS header value.
            referrer_policy: Referrer-Policy header value.
            permissions_policy: Permissions-Policy header value (optional).
        """
        super().__init__(app)
        self.headers = {
            "X-Frame-Options": x_frame_options,
            "X-Content-Type-Options": x_content_type_options,
            "X-XSS-Protection": x_xss_protection,
            "Strict-Transport-Security": strict_transport_security,
            "Referrer-Policy": referrer_policy,
        }
        if content_security_policy:
            self.headers["Content-Security-Policy"] = content_security_policy
        if permissions_policy:
            self.headers["Permissions-Policy"] = permissions_policy

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Add security headers to the response.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler in chain.

        Returns:
            Response with security headers added.
        """
        correlation_id = getattr(request.state, "correlation_id", None)

        response = await call_next(request)

        for header_name, header_value in self.headers.items():
            response.headers[header_name] = header_value

        logger.debug(
            "security_headers_applied",
            correlation_id=correlation_id,
            path=request.url.path,
            headers_count=len(self.headers),
        )

        return response
