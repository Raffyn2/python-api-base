"""Multitenancy middleware for tenant context resolution.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 18.1**
**Refactored: Split from production.py for one-class-per-file compliance**
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.multitenancy import (
    TenantContext,
    TenantInfo,
    TenantResolutionStrategy,
)

logger = logging.getLogger(__name__)


@dataclass
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
                return Response(
                    content='{"error": "Tenant ID required"}',
                    status_code=400,
                    media_type="application/json",
                )
            tenant_id = self._config.default_tenant_id

        # Set tenant context
        if tenant_id:
            tenant = TenantInfo[str](
                id=tenant_id,
                name=f"Tenant {tenant_id}",
            )
            TenantContext.set_current(tenant)
            logger.debug(f"Tenant context set: {tenant_id}")

        try:
            return await call_next(request)
        finally:
            # Clear tenant context
            TenantContext.set_current(None)
