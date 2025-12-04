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

from infrastructure.idempotency.errors import IdempotencyKeyConflictError
from infrastructure.idempotency.handler import (
    IdempotencyConfig,
    IdempotencyHandler,
    compute_request_hash,
)

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

    def _create_error_response(self, error_type: str, title: str, detail: str, status: int) -> JSONResponse:
        """Create standardized error response."""
        return JSONResponse(
            status_code=status,
            content={
                "type": f"https://api.example.com/errors/{error_type}",
                "title": title,
                "status": status,
                "detail": detail,
            },
        )

    def _create_conflict_response(self) -> JSONResponse:
        """Create idempotency conflict response."""
        return self._create_error_response(
            error_type="idempotency-conflict",
            title="Idempotency Key Conflict",
            detail="Idempotency key was already used with a different request body",
            status=422,
        )

    def _create_key_missing_response(self) -> JSONResponse:
        """Create idempotency key missing response."""
        return self._create_error_response(
            error_type="idempotency-key-missing",
            title="Idempotency Key Required",
            detail="Idempotency-Key header is required for this endpoint",
            status=400,
        )

    async def _handle_cached_record(
        self,
        record: Any,
        request_hash: str,
        idempotency_key: str,
        path: str,
    ) -> Response | None:
        """Handle existing idempotency record. Returns response or None if conflict."""
        if record.request_hash != request_hash:
            logger.warning(
                "Idempotency key conflict",
                extra={"key": idempotency_key, "path": path},
            )
            return self._create_conflict_response()

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

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Process request with idempotency handling.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.1, 23.5**
        """
        if not self._should_handle(request):
            return await call_next(request)

        handler = self._get_handler(request)
        if handler is None:
            return await call_next(request)

        idempotency_key = request.headers.get(self._config.header_name)

        if idempotency_key is None:
            if self._is_required(request.url.path):
                return self._create_key_missing_response()
            return await call_next(request)

        body = await request.body()
        request_hash = compute_request_hash(
            method=request.method,
            path=request.url.path,
            body=body,
            content_type=request.headers.get("content-type"),
        )

        try:
            record = await handler.get_record(idempotency_key)

            if record is not None:
                return await self._handle_cached_record(
                    record, request_hash, idempotency_key, request.url.path
                )

            response = await call_next(request)
            return await self._store_and_return_response(
                handler, idempotency_key, request_hash, response
            )

        except IdempotencyKeyConflictError:
            return self._create_conflict_response()
        except Exception as e:
            logger.error(f"Idempotency handling failed: {e}")
            return await call_next(request)

    async def _store_and_return_response(
        self,
        handler: IdempotencyHandler,
        idempotency_key: str,
        request_hash: str,
        response: Response,
    ) -> Response:
        """Store successful response and return it."""
        if not (200 <= response.status_code < 300):
            return response

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        await handler.store_record(
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_body=response_body.decode(),
            status_code=response.status_code,
        )

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

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
