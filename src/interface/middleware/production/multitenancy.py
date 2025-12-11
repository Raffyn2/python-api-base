"""Multitenancy middleware for tenant context resolution.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 18.1**
**Refactored: Split from production.py for one-class-per-file compliance**
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.multitenancy import (
    TenantContext,
    TenantInfo,
    TenantResolutionStrategy,
)

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class MultitenancyConfig:
    """Configuration for multitenancy middleware."""

    strategy: TenantResolutionStrategy = TenantResolutionStrategy.HEADER
    header_name: str = "X-Tenant-ID"
    required: bool = False
    default_tenant_id: str | None = None


class MultitenancyMiddleware(BaseHTTPMiddleware):
    """Middleware that resolves and sets tenant context.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 18.1**

    Usage:
        app.add_middleware(MultitenancyMiddleware, config=MultitenancyConfig())
    """

    def __init__(self, app: Any, config: MultitenancyConfig | None = None) -> None:
        super().__init__(app)
        self._config = config or MultitenancyConfig()
        self._context = TenantContext[str](
            strategy=self._config.strategy,
            header_name=self._config.header_name,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with tenant context."""
        # Resolve tenant ID from headers
        tenant_id = request.headers.get(self._config.header_name)

        if tenant_id is None:
            if self._config.required:
                from core.errors.http import PROBLEM_JSON_MEDIA_TYPE, ProblemDetail

                problem = ProblemDetail(
                    type="https://api.example.com/errors/TENANT_REQUIRED",
                    title="Tenant ID Required",
                    status=400,
                    detail=f"Header '{self._config.header_name}' is required",
                    instance=str(request.url),
                )
                return Response(
                    content=problem.model_dump_json(),
                    status_code=400,
                    media_type=PROBLEM_JSON_MEDIA_TYPE,
                )
            tenant_id = self._config.default_tenant_id

        # Get correlation_id for logging
        correlation_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")

        # Set tenant context
        if tenant_id:
            tenant = TenantInfo[str](
                id=tenant_id,
                name=f"Tenant {tenant_id}",
            )
            TenantContext.set_current(tenant)
            logger.debug(
                "tenant_context_set",
                correlation_id=correlation_id,
                tenant_id=tenant_id,
            )

        try:
            return await call_next(request)
        finally:
            # Clear tenant context
            TenantContext.set_current(None)
