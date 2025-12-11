"""Audit middleware for request/response audit trail.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 22.1, 22.4**
**Refactored: Split from production.py for one-class-per-file compliance**
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.audit import (
    AuditAction,
    AuditRecord,
    AuditStore,
)

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class AuditConfig:
    """Configuration for audit middleware."""

    enabled: bool = True
    log_request_body: bool = False
    log_response_body: bool = False
    exclude_paths: set[str] | None = None


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that creates audit records for all requests.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 22.1, 22.4**

    Usage:
        store = InMemoryAuditStore()
        app.add_middleware(AuditMiddleware, store=store)
    """

    def __init__(
        self,
        app: Any,
        store: AuditStore[Any],
        config: AuditConfig | None = None,
    ) -> None:
        super().__init__(app)
        self._store = store
        self._config = config or AuditConfig()
        self._exclude = self._config.exclude_paths or {"/health", "/metrics", "/docs"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and create audit record."""
        if not self._config.enabled:
            return await call_next(request)

        # Skip excluded paths
        if request.url.path in self._exclude:
            return await call_next(request)

        # Get correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        user_id = request.headers.get("X-User-ID")

        # Map HTTP method to audit action
        action_map = {
            "GET": AuditAction.READ,
            "POST": AuditAction.CREATE,
            "PUT": AuditAction.UPDATE,
            "PATCH": AuditAction.UPDATE,
            "DELETE": AuditAction.DELETE,
        }
        action = action_map.get(request.method, AuditAction.READ)

        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Create audit record
            record = AuditRecord[dict](
                entity_type="http_request",
                entity_id=request.url.path,
                action=action,
                user_id=user_id,
                correlation_id=correlation_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            await self._store.save(record)
            logger.debug(
                "audit_record_created",
                correlation_id=correlation_id,
                record_id=record.id,
                path=request.url.path,
            )

            return response

        except Exception as e:
            # Create error audit record
            record = AuditRecord[dict](
                entity_type="http_request",
                entity_id=request.url.path,
                action=action,
                user_id=user_id,
                correlation_id=correlation_id,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "error": type(e).__name__,  # Don't expose full error message
                },
            )
            await self._store.save(record)
            logger.warning(
                "audit_record_error",
                correlation_id=correlation_id,
                path=request.url.path,
                error_type=type(e).__name__,
            )
            raise
