"""Generic Middleware Chain for composable request processing.

This module provides a generic middleware chain pattern for
composable and configurable request/response processing.

**Feature: api-architecture-analysis**
**Validates: Requirements 4.4**
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self

import structlog

logger = structlog.get_logger(__name__)


class MiddlewarePriority(Enum):
    """Priority levels for middleware ordering."""

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


@dataclass(slots=True)
class MiddlewareContext[ContextT]:
    """Context passed through middleware chain."""

    data: ContextT
    metadata: dict[str, Any] = field(default_factory=dict)
    should_continue: bool = True
    error: Exception | None = None

    def stop(self) -> None:
        """Stop middleware chain execution."""
        self.should_continue = False

    def set_error(self, error: Exception) -> None:
        """Set error and stop chain."""
        self.error = error
        self.should_continue = False


# Type alias for next handler
NextHandler = Callable[[MiddlewareContext[Any]], Awaitable[MiddlewareContext[Any]]]


class Middleware[ContextT](ABC):
    """Abstract base class for middleware."""

    def __init__(
        self,
        name: str = "",
        priority: MiddlewarePriority = MiddlewarePriority.NORMAL,
        enabled: bool = True,
    ) -> None:
        self.name = name or self.__class__.__name__
        self.priority = priority
        self.enabled = enabled

    @abstractmethod
    async def process(
        self,
        context: MiddlewareContext[ContextT],
        next_handler: NextHandler,
    ) -> MiddlewareContext[ContextT]:
        """Process the context and call next handler."""
        ...

    async def __call__(
        self,
        context: MiddlewareContext[ContextT],
        next_handler: NextHandler,
    ) -> MiddlewareContext[ContextT]:
        """Make middleware callable."""
        if not self.enabled:
            return await next_handler(context)
        return await self.process(context, next_handler)


class FunctionMiddleware[ContextT](Middleware[ContextT]):
    """Middleware created from a function."""

    def __init__(
        self,
        func: Callable[
            [MiddlewareContext[ContextT], NextHandler],
            Awaitable[MiddlewareContext[ContextT]],
        ],
        name: str = "",
        priority: MiddlewarePriority = MiddlewarePriority.NORMAL,
    ) -> None:
        super().__init__(name or func.__name__, priority)
        self._func = func

    async def process(
        self,
        context: MiddlewareContext[ContextT],
        next_handler: NextHandler,
    ) -> MiddlewareContext[ContextT]:
        """Process using the wrapped function."""
        return await self._func(context, next_handler)


class MiddlewareChain[ContextT]:
    """Composable middleware chain."""

    def __init__(self) -> None:
        self._middlewares: list[Middleware[ContextT]] = []
        self._sorted = False

    def add(self, middleware: Middleware[ContextT]) -> Self:
        """Add middleware to the chain."""
        self._middlewares.append(middleware)
        self._sorted = False
        return self

    def add_function(
        self,
        func: Callable[
            [MiddlewareContext[ContextT], NextHandler],
            Awaitable[MiddlewareContext[ContextT]],
        ],
        name: str = "",
        priority: MiddlewarePriority = MiddlewarePriority.NORMAL,
    ) -> Self:
        """Add a function as middleware."""
        return self.add(FunctionMiddleware(func, name, priority))

    def remove(self, name: str) -> bool:
        """Remove middleware by name."""
        initial_len = len(self._middlewares)
        self._middlewares = [m for m in self._middlewares if m.name != name]
        return len(self._middlewares) < initial_len

    def enable(self, name: str) -> bool:
        """Enable middleware by name."""
        for m in self._middlewares:
            if m.name == name:
                m.enabled = True
                return True
        return False

    def disable(self, name: str) -> bool:
        """Disable middleware by name."""
        for m in self._middlewares:
            if m.name == name:
                m.enabled = False
                return True
        return False

    def _sort(self) -> None:
        """Sort middlewares by priority."""
        if not self._sorted:
            self._middlewares.sort(key=lambda m: m.priority.value)
            self._sorted = True

    async def execute(
        self,
        context: MiddlewareContext[ContextT],
        final_handler: Callable[[MiddlewareContext[ContextT]], Awaitable[MiddlewareContext[ContextT]]] | None = None,
    ) -> MiddlewareContext[ContextT]:
        """Execute the middleware chain."""
        self._sort()

        async def default_final(
            ctx: MiddlewareContext[ContextT],
        ) -> MiddlewareContext[ContextT]:
            return ctx

        handler = final_handler or default_final

        # Build chain from end to start
        for middleware in reversed(self._middlewares):
            if middleware.enabled:
                current_handler = handler
                current_middleware = middleware

                async def make_handler(
                    mw: Middleware[ContextT],
                    next_h: Callable[
                        [MiddlewareContext[ContextT]],
                        Awaitable[MiddlewareContext[ContextT]],
                    ],
                ) -> Callable[
                    [MiddlewareContext[ContextT]],
                    Awaitable[MiddlewareContext[ContextT]],
                ]:
                    async def wrapped(
                        ctx: MiddlewareContext[ContextT],
                    ) -> MiddlewareContext[ContextT]:
                        if not ctx.should_continue:
                            return ctx
                        return await mw(ctx, next_h)

                    return wrapped

                handler = await make_handler(current_middleware, current_handler)

        return await handler(context)

    @property
    def middlewares(self) -> list[Middleware[ContextT]]:
        """Get list of middlewares."""
        self._sort()
        return list(self._middlewares)

    def __len__(self) -> int:
        return len(self._middlewares)


class MiddlewareChainBuilder[ContextT]:
    """Fluent builder for MiddlewareChain."""

    def __init__(self) -> None:
        self._chain: MiddlewareChain[ContextT] = MiddlewareChain()

    def use(self, middleware: Middleware[ContextT]) -> Self:
        """Add middleware."""
        self._chain.add(middleware)
        return self

    def use_function(
        self,
        func: Callable[
            [MiddlewareContext[ContextT], NextHandler],
            Awaitable[MiddlewareContext[ContextT]],
        ],
        name: str = "",
        priority: MiddlewarePriority = MiddlewarePriority.NORMAL,
    ) -> Self:
        """Add function as middleware."""
        self._chain.add_function(func, name, priority)
        return self

    def build(self) -> MiddlewareChain[ContextT]:
        """Build the chain."""
        return self._chain


# Common middleware implementations
class LoggingMiddleware(Middleware[Any]):
    """Middleware that logs request/response using structlog."""

    def __init__(
        self,
        priority: MiddlewarePriority = MiddlewarePriority.HIGHEST,
    ) -> None:
        super().__init__("logging", priority)

    async def process(
        self,
        context: MiddlewareContext[Any],
        next_handler: NextHandler,
    ) -> MiddlewareContext[Any]:
        """Log and pass through."""
        correlation_id = context.metadata.get("correlation_id")
        logger.debug(
            "middleware_chain_processing",
            correlation_id=correlation_id,
            metadata_keys=list(context.metadata.keys()),
        )
        result = await next_handler(context)
        logger.debug(
            "middleware_chain_completed",
            correlation_id=correlation_id,
            has_error=result.error is not None,
        )
        return result


class ErrorHandlerMiddleware(Middleware[Any]):
    """Middleware that catches and handles errors."""

    def __init__(
        self,
        error_handler: Callable[[Exception], Any] | None = None,
        priority: MiddlewarePriority = MiddlewarePriority.HIGHEST,
    ) -> None:
        super().__init__("error_handler", priority)
        self._error_handler = error_handler

    async def process(
        self,
        context: MiddlewareContext[Any],
        next_handler: NextHandler,
    ) -> MiddlewareContext[Any]:
        """Catch errors and handle them."""
        correlation_id = context.metadata.get("correlation_id")
        try:
            return await next_handler(context)
        except Exception as e:
            logger.error(
                "middleware_chain_error",
                correlation_id=correlation_id,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            context.set_error(e)
            if self._error_handler:
                self._error_handler(e)
            return context


# Convenience factory
def create_middleware_chain() -> MiddlewareChain[Any]:
    """Create an empty middleware chain."""
    return MiddlewareChain()
