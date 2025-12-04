"""Fallback pattern implementation.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.4**
"""

from collections.abc import Awaitable, Callable


class Fallback[T, TFallback]:
    """Generic fallback pattern for graceful degradation.

    Type Parameters:
        T: Primary operation return type.
        TFallback: Fallback value type.
    """

    def __init__(
        self,
        fallback_value: TFallback | None = None,
        fallback_func: Callable[[], Awaitable[TFallback]] | None = None,
    ) -> None:
        self._fallback_value = fallback_value
        self._fallback_func = fallback_func

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T | TFallback:
        """Execute with fallback on failure.

        Returns:
            Primary result or fallback value.
        """
        try:
            return await func()
        except Exception:
            if self._fallback_func:
                return await self._fallback_func()
            if self._fallback_value is not None:
                return self._fallback_value
            raise
