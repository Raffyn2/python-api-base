"""Idempotency middleware for FastAPI.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 23.1, 23.5, 23.6**

Provides automatic idempotency handling for POST/PATCH requests.
"""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .errors import IdempotencyKeyConflictError
from .handler import IdempotencyConfig, IdempotencyHandler, compute_request_hash

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for idempotent request handling.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.1, 23.5, 23.6**

    Automatically handles Idempotency-Key header for POST/PATCH requests:
    - Returns cached response for duplicate requests
    - Stores response for new requests
    - Rejects conflicting key reuse with 422

    Example:
        >>> app.add_middleware(
        ...     IdempotencyMiddleware,
        ...     handler=IdempotencyHandler(redis_url),
        ...     required_endpoints={"/api/v1/payments", "/api/v1/orders"},
        ... )
    """

    def __init__(
        self,
        app: Any,
        handler: IdempotencyHandler | None = None,
        methods: set[str] | None = None,
        required_endpoints: set[str] | None = None,
        exclude_paths: set[str] | None = None,
        config: IdempotencyConfig | None = None,
    ) -> None:
        """Initialize idempotency middleware.

        Args:
            app: FastAPI application.
            handler: Idempotency handler instance (or fetched from app.state).
            methods: HTTP methods to handle (default: POST, PATCH, PUT).
            required_endpoints: Endpoints that require idempotency key.
            exclude_paths: Paths to exclude from idempotency handling.
            config: Configuration (if handler not provided).

        Note:
            If handler is None, the middleware will try to get it from
            app.state.idempotency_handler on each request.
        """
        super().__init__(app)
        self._handler = handler
        self._methods = methods or {"POST", "PATCH", "PUT"}
        self._required_endpoints = required_endpoints or set()
        self._exclude_paths = exclude_paths or {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
        }
        self._config = config or (handler._config if handler else IdempotencyConfig())

    def _get_handler(self, request: Request) -> IdempotencyHandler | None:
        """Get idempotency handler (from init or app.state)."""
        if self._handler is not None:
            return self._handler
        return getattr(request.app.state, "idempotency_handler", None)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Process request with idempotency handling.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.1, 23.5**
        """
        # Check if idempotency applies
        if not self._should_handle(request):
            return await call_next(request)

        # Get handler (may be None if Redis not available)
        handler = self._get_handler(request)
        if handler is None:
            # No handler available, proceed without idempotency
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get(self._config.header_name)

        # Check if key is required
        if idempotency_key is None:
            if self._is_required(request.url.path):
                return JSONResponse(
                    status_code=400,
                    content={
                        "type": "https://api.example.com/errors/idempotency-key-missing",
                        "title": "Idempotency Key Required",
                        "status": 400,
                        "detail": "Idempotency-Key header is required for this endpoint",
                    },
                )
            # Key not required and not provided - proceed normally
            return await call_next(request)

        # Read and hash request body
        body = await request.body()
        request_hash = compute_request_hash(
            method=request.method,
            path=request.url.path,
            body=body,
            content_type=request.headers.get("content-type"),
        )

        try:
            # Check for existing record
            record = await handler.get_record(idempotency_key)

            if record is not None:
                # Check for conflict
                if record.request_hash != request_hash:
                    logger.warning(
                        "Idempotency key conflict",
                        extra={"key": idempotency_key, "path": request.url.path},
                    )
                    return JSONResponse(
                        status_code=422,
                        content={
                            "type": "https://api.example.com/errors/idempotency-conflict",
                            "title": "Idempotency Key Conflict",
                            "status": 422,
                            "detail": "Idempotency key was already used with a different request body",
                        },
                    )

                # Return cached response
                logger.info(
                    "Replaying idempotent response",
                    extra={"key": idempotency_key, "status": record.status_code},
                )
                return Response(
                    content=record.response_body,
                    status_code=record.status_code,
                    headers={
                        self._config.replay_header: "true",
                        "Content-Type": "application/json",
                    },
                )

            # Execute request
            response = await call_next(request)

            # Store response for successful operations
            if 200 <= response.status_code < 300:
                # Read response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Store in Redis
                await handler.store_record(
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    response_body=response_body.decode(),
                    status_code=response.status_code,
                )

                # Return new response with body
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

            return response

        except IdempotencyKeyConflictError:
            return JSONResponse(
                status_code=422,
                content={
                    "type": "https://api.example.com/errors/idempotency-conflict",
                    "title": "Idempotency Key Conflict",
                    "status": 422,
                    "detail": "Idempotency key was already used with a different request body",
                },
            )
        except Exception as e:
            logger.error(f"Idempotency handling failed: {e}")
            # Proceed without idempotency on error
            return await call_next(request)

    def _should_handle(self, request: Request) -> bool:
        """Check if request should be handled for idempotency."""
        # Check method
        if request.method not in self._methods:
            return False

        # Check excluded paths
        for path in self._exclude_paths:
            if request.url.path.startswith(path):
                return False

        return True

    def _is_required(self, path: str) -> bool:
        """Check if idempotency key is required for path."""
        for required_path in self._required_endpoints:
            if path.startswith(required_path):
                return True
        return False
