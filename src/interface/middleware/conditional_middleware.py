"""Conditional Middleware for selective route-based middleware application.

This module provides conditional middleware that can be applied
selectively based on route patterns, HTTP methods, or custom conditions.

**Feature: api-architecture-analysis**
**Validates: Requirements 4.4**
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self

import structlog

logger = structlog.get_logger(__name__)

# Security limits to prevent ReDoS attacks
MAX_REGEX_LENGTH = 500


class HttpMethod(Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    ALL = "*"


@dataclass(slots=True)
class RouteInfo:
    """Information about the current route."""

    path: str
    method: HttpMethod
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class Condition(ABC):
    """Abstract base class for middleware conditions."""

    @abstractmethod
    def matches(self, route_info: RouteInfo) -> bool:
        """Check if condition matches the route."""
        ...

    def __and__(self, other: "Condition") -> "AndCondition":
        """Combine conditions with AND."""
        return AndCondition(self, other)

    def __or__(self, other: "Condition") -> "OrCondition":
        """Combine conditions with OR."""
        return OrCondition(self, other)

    def __invert__(self) -> "NotCondition":
        """Negate condition."""
        return NotCondition(self)


class PathCondition(Condition):
    """Condition based on path pattern."""

    def __init__(self, pattern: str, regex: bool = False) -> None:
        self._pattern = pattern
        self._regex = regex
        self._compiled: re.Pattern | None = None

        # Validate pattern length to prevent ReDoS
        if len(pattern) > MAX_REGEX_LENGTH:
            logger.warning(
                "path_pattern_too_long",
                pattern_length=len(pattern),
                max_length=MAX_REGEX_LENGTH,
            )
            return

        try:
            if regex:
                self._compiled = re.compile(pattern)
            else:
                # Convert glob-like pattern to regex
                regex_pattern = pattern.replace("*", ".*").replace("?", ".")
                self._compiled = re.compile(f"^{regex_pattern}$")
        except re.error:
            logger.warning("invalid_path_pattern", pattern=pattern[:50], exc_info=True)

    def matches(self, route_info: RouteInfo) -> bool:
        """Check if path matches pattern."""
        if self._compiled is None:
            return False
        return bool(self._compiled.match(route_info.path))


class MethodCondition(Condition):
    """Condition based on HTTP method."""

    def __init__(self, *methods: HttpMethod) -> None:
        self._methods = set(methods)

    def matches(self, route_info: RouteInfo) -> bool:
        """Check if method matches."""
        if HttpMethod.ALL in self._methods:
            return True
        return route_info.method in self._methods


class HeaderCondition(Condition):
    """Condition based on header presence or value."""

    def __init__(self, header: str, value: str | None = None) -> None:
        self._header = header.lower()
        self._value = value

    def matches(self, route_info: RouteInfo) -> bool:
        """Check if header matches."""
        headers_lower = {k.lower(): v for k, v in route_info.headers.items()}
        if self._header not in headers_lower:
            return False
        if self._value is None:
            return True
        return headers_lower[self._header] == self._value


class AndCondition(Condition):
    """Combines two conditions with AND logic."""

    def __init__(self, left: Condition, right: Condition) -> None:
        self._left = left
        self._right = right

    def matches(self, route_info: RouteInfo) -> bool:
        """Check if both conditions match."""
        return self._left.matches(route_info) and self._right.matches(route_info)


class OrCondition(Condition):
    """Combines two conditions with OR logic."""

    def __init__(self, left: Condition, right: Condition) -> None:
        self._left = left
        self._right = right

    def matches(self, route_info: RouteInfo) -> bool:
        """Check if either condition matches."""
        return self._left.matches(route_info) or self._right.matches(route_info)


class NotCondition(Condition):
    """Negates a condition."""

    def __init__(self, condition: Condition) -> None:
        self._condition = condition

    def matches(self, route_info: RouteInfo) -> bool:
        """Check if condition does not match."""
        return not self._condition.matches(route_info)


class CustomCondition(Condition):
    """Condition based on custom function."""

    def __init__(self, func: Callable[[RouteInfo], bool]) -> None:
        self._func = func

    def matches(self, route_info: RouteInfo) -> bool:
        """Check using custom function."""
        return self._func(route_info)


class AlwaysCondition(Condition):
    """Condition that always matches."""

    def matches(self, route_info: RouteInfo) -> bool:
        return True


class NeverCondition(Condition):
    """Condition that never matches."""

    def matches(self, route_info: RouteInfo) -> bool:
        return False


# Type alias for middleware function
type MiddlewareFunc[RequestT, ResponseT] = Callable[
    [RequestT, Callable[[RequestT], Awaitable[ResponseT]]], Awaitable[ResponseT]
]


@dataclass(slots=True)
class ConditionalMiddleware[RequestT, ResponseT]:
    """Middleware that executes conditionally based on route info."""

    middleware: "MiddlewareFunc[RequestT, ResponseT]"
    condition: Condition
    name: str = ""
    enabled: bool = True

    async def __call__(
        self,
        request: RequestT,
        route_info: RouteInfo,
        next_handler: Callable[[RequestT], Awaitable[ResponseT]],
    ) -> ResponseT:
        """Execute middleware if condition matches."""
        if not self.enabled:
            return await next_handler(request)

        if self.condition.matches(route_info):
            return await self.middleware(request, next_handler)
        return await next_handler(request)


class ConditionalMiddlewareRegistry[RequestT, ResponseT]:
    """Registry for conditional middlewares."""

    def __init__(self) -> None:
        self._middlewares: list[ConditionalMiddleware[RequestT, ResponseT]] = []

    def register(
        self,
        middleware: MiddlewareFunc[RequestT, ResponseT],
        condition: Condition,
        name: str = "",
    ) -> Self:
        """Register a conditional middleware."""
        self._middlewares.append(
            ConditionalMiddleware(
                middleware=middleware,
                condition=condition,
                name=name or middleware.__name__ if hasattr(middleware, "__name__") else "",
            )
        )
        return self

    def for_path(
        self,
        pattern: str,
        middleware: MiddlewareFunc[RequestT, ResponseT],
        name: str = "",
    ) -> Self:
        """Register middleware for path pattern."""
        return self.register(middleware, PathCondition(pattern), name)

    def for_methods(
        self,
        methods: list[HttpMethod],
        middleware: MiddlewareFunc[RequestT, ResponseT],
        name: str = "",
    ) -> Self:
        """Register middleware for specific HTTP methods."""
        return self.register(middleware, MethodCondition(*methods), name)

    def for_api(
        self,
        middleware: MiddlewareFunc[RequestT, ResponseT],
        name: str = "",
    ) -> Self:
        """Register middleware for /api/* paths."""
        return self.register(middleware, PathCondition("/api/*"), name)

    def except_path(
        self,
        pattern: str,
        middleware: MiddlewareFunc[RequestT, ResponseT],
        name: str = "",
    ) -> Self:
        """Register middleware for all paths except pattern."""
        return self.register(middleware, ~PathCondition(pattern), name)

    async def execute(
        self,
        request: RequestT,
        route_info: RouteInfo,
        final_handler: Callable[[RequestT], Awaitable[ResponseT]],
        correlation_id: str | None = None,
    ) -> ResponseT:
        """Execute all matching middlewares."""
        handler = final_handler
        matching_count = 0

        for mw in reversed(self._middlewares):
            if mw.enabled and mw.condition.matches(route_info):
                matching_count += 1
                current_mw = mw.middleware
                current_handler = handler

                async def make_handler(
                    middleware: MiddlewareFunc[RequestT, ResponseT],
                    next_h: Callable[[RequestT], Awaitable[ResponseT]],
                ) -> Callable[[RequestT], Awaitable[ResponseT]]:
                    async def wrapped(req: RequestT) -> ResponseT:
                        return await middleware(req, next_h)

                    return wrapped

                handler = await make_handler(current_mw, current_handler)

        if matching_count > 0:
            logger.debug(
                "conditional_middleware_executed",
                correlation_id=correlation_id,
                path=route_info.path,
                method=route_info.method.value,
                matching_middlewares=matching_count,
            )

        return await handler(request)

    def get_matching(self, route_info: RouteInfo) -> list[ConditionalMiddleware[RequestT, ResponseT]]:
        """Get all middlewares matching the route."""
        return [mw for mw in self._middlewares if mw.enabled and mw.condition.matches(route_info)]

    def __len__(self) -> int:
        return len(self._middlewares)


# Convenience functions
def path(pattern: str) -> PathCondition:
    """Create a path condition."""
    return PathCondition(pattern)


def method(*methods: HttpMethod) -> MethodCondition:
    """Create a method condition."""
    return MethodCondition(*methods)


def header(name: str, value: str | None = None) -> HeaderCondition:
    """Create a header condition."""
    return HeaderCondition(name, value)


def custom(func: Callable[[RouteInfo], bool]) -> CustomCondition:
    """Create a custom condition."""
    return CustomCondition(func)


def always() -> AlwaysCondition:
    """Create an always-matching condition."""
    return AlwaysCondition()


def never() -> NeverCondition:
    """Create a never-matching condition."""
    return NeverCondition()
