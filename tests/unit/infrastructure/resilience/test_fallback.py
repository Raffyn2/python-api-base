"""Unit tests for Fallback pattern.

Tests fallback value and function behavior.
"""

import pytest

from infrastructure.resilience.fallback import Fallback


class TestFallback:
    """Tests for Fallback class."""

    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        """Test execute returns primary result on success."""
        fallback = Fallback[str, str](fallback_value="fallback")

        async def operation() -> str:
            return "primary"

        result = await fallback.execute(operation)

        assert result == "primary"

    @pytest.mark.asyncio
    async def test_execute_fallback_value(self) -> None:
        """Test execute returns fallback value on failure."""
        fallback = Fallback[str, str](fallback_value="fallback")

        async def operation() -> str:
            raise ValueError("error")

        result = await fallback.execute(operation)

        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_execute_fallback_func(self) -> None:
        """Test execute calls fallback function on failure."""
        async def fallback_func() -> str:
            return "from_func"

        fallback = Fallback[str, str](fallback_func=fallback_func)

        async def operation() -> str:
            raise ValueError("error")

        result = await fallback.execute(operation)

        assert result == "from_func"

    @pytest.mark.asyncio
    async def test_execute_fallback_func_priority(self) -> None:
        """Test fallback function takes priority over value."""
        async def fallback_func() -> str:
            return "from_func"

        fallback = Fallback[str, str](
            fallback_value="from_value", fallback_func=fallback_func
        )

        async def operation() -> str:
            raise ValueError("error")

        result = await fallback.execute(operation)

        assert result == "from_func"

    @pytest.mark.asyncio
    async def test_execute_no_fallback_raises(self) -> None:
        """Test execute raises when no fallback configured."""
        fallback = Fallback[str, str]()

        async def operation() -> str:
            raise ValueError("error")

        with pytest.raises(ValueError, match="error"):
            await fallback.execute(operation)

    @pytest.mark.asyncio
    async def test_execute_with_different_types(self) -> None:
        """Test execute with different primary and fallback types."""
        fallback = Fallback[int, str](fallback_value="not_found")

        async def operation() -> int:
            raise ValueError("error")

        result = await fallback.execute(operation)

        assert result == "not_found"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_execute_fallback_value_none(self) -> None:
        """Test execute raises when fallback value is None."""
        fallback = Fallback[str, str](fallback_value=None)

        async def operation() -> str:
            raise ValueError("error")

        with pytest.raises(ValueError, match="error"):
            await fallback.execute(operation)

    @pytest.mark.asyncio
    async def test_execute_async_fallback_func(self) -> None:
        """Test execute with async fallback function."""
        call_count = 0

        async def fallback_func() -> str:
            nonlocal call_count
            call_count += 1
            return f"fallback_{call_count}"

        fallback = Fallback[str, str](fallback_func=fallback_func)

        async def operation() -> str:
            raise ValueError("error")

        result1 = await fallback.execute(operation)
        result2 = await fallback.execute(operation)

        assert result1 == "fallback_1"
        assert result2 == "fallback_2"
