"""Resilience middleware with circuit breaker pattern.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.1**
**Refactored: Split from production.py for one-class-per-file compliance**
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.resilience import CircuitBreaker, CircuitBreakerConfig, CircuitState

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class ResilienceConfig:
    """Configuration for resilience middleware."""

    failure_threshold: int = 5
    timeout: timedelta = timedelta(seconds=30.0)
    enabled: bool = True


class ResilienceMiddleware(BaseHTTPMiddleware):
    """Middleware that applies circuit breaker pattern to requests.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.1**

    Usage:
        app.add_middleware(ResilienceMiddleware, config=ResilienceConfig())
    """

    def __init__(self, app: Any, config: ResilienceConfig | None = None) -> None:
        super().__init__(app)
        self._config = config or ResilienceConfig()
        self._circuit = CircuitBreaker(
            "production_middleware",
            CircuitBreakerConfig(
                failure_threshold=self._config.failure_threshold,
                timeout=self._config.timeout,
            ),
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with circuit breaker protection."""
        if not self._config.enabled:
            return await call_next(request)

        # Get correlation_id for logging
        correlation_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")

        # Check circuit state
        if not self._circuit._can_execute():
            logger.warning(
                "circuit_breaker_open",
                correlation_id=correlation_id,
                path=request.url.path,
                state=CircuitState.OPEN.value,
            )
            from core.errors.http import PROBLEM_JSON_MEDIA_TYPE, ProblemDetail

            problem = ProblemDetail.service_unavailable(
                service="api",
                retry_after=int(self._config.timeout.total_seconds()),
            )
            return Response(
                content=problem.model_dump_json(),
                status_code=503,
                media_type=PROBLEM_JSON_MEDIA_TYPE,
            )

        try:
            response = await call_next(request)
            if response.status_code < 500:
                self._circuit._record_success()
            else:
                self._circuit._record_failure()
            return response
        except Exception:
            self._circuit._record_failure()
            logger.exception(
                "request_failed",
                correlation_id=correlation_id,
                path=request.url.path,
            )
            raise
