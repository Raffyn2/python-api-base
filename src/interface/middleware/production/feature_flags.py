"""Feature flag middleware for request context.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 19.2**
**Refactored: Split from production.py for one-class-per-file compliance**
"""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.feature_flags import (
    EvaluationContext,
    FeatureFlagEvaluator,
)


class FeatureFlagMiddleware(BaseHTTPMiddleware):
    """Middleware that provides feature flag evaluation in request context.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 19.2**

    Usage:
        evaluator = FeatureFlagEvaluator()
        evaluator.register(FeatureFlag(key="new_api", ...))
        app.add_middleware(FeatureFlagMiddleware, evaluator=evaluator)
    """

    def __init__(self, app: Any, evaluator: FeatureFlagEvaluator[Any]) -> None:
        super().__init__(app)
        self._evaluator = evaluator

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with feature flag context."""
        # Extract user ID from request (from auth header, JWT, etc.)
        user_id = request.headers.get("X-User-ID")

        # Create evaluation context
        context = EvaluationContext[dict](
            user_id=user_id,
            attributes={
                "path": request.url.path,
                "method": request.method,
            },
        )

        # Store evaluator and context in request state
        request.state.feature_flags = self._evaluator
        request.state.feature_context = context

        return await call_next(request)


def is_feature_enabled(request: Request, flag_key: str) -> bool:
    """Check if feature is enabled for current request.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 19.2**

    Usage in route handlers:
        @app.get("/items")
        async def list_items(request: Request):
            if is_feature_enabled(request, "new_items_api"):
                return new_items_response()
            return old_items_response()
    """
    evaluator = getattr(request.state, "feature_flags", None)
    context = getattr(request.state, "feature_context", None)

    if evaluator is None or context is None:
        return False

    return evaluator.is_enabled(flag_key, context)
