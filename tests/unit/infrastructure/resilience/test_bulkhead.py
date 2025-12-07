"""Unit tests for Bulkhead pattern.

Tests bulkhead isolation, concurrency limits, and statistics.
"""

import asyncio

import pytest

from infrastructure.resilience.bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadRejectedError,
    BulkheadRegistry,
    BulkheadState,
    BulkheadStats,
    bulkhead,
)


class TestBulkheadState:
    """Tests for BulkheadState enum."""

    def test_accepting_value(self) -> None:
        """Test ACCEPTING value."""
        assert BulkheadState.ACCEPTING.value == "accepting"

    def test_rejecting_value(self) -> None:
        """Test REJECTING value."""
        assert BulkheadState.REJECTING.value == "rejecting"


class TestBulkheadRejectedError:
    """Tests for BulkheadRejectedError."""

    def test_error_message(self) -> None:
        """Test error message includes name."""
        error = BulkheadRejectedError("test-bulkhead")

        assert "test-bulkhead" in str(error)
        assert error.name == "test-bulkhead"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = BulkheadRejectedError("test", message="Custom message")

        assert "Custom message" in str(error)


class TestBulkheadConfig:
    """Tests for BulkheadConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BulkheadConfig()

        assert config.max_concurrent == 10
        assert config.max_wait_seconds == 5.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BulkheadConfig(max_concurrent=5, max_wait_seconds=2.0)

        assert config.max_concurrent == 5
        assert config.max_wait_seconds == 2.0


class TestBulkheadStats:
    """Tests for BulkheadStats."""

    def test_available_permits(self) -> None:
        """Test available permits calculation."""
        stats = BulkheadStats(
            name="test", max_concurrent=10, current_concurrent=3
        )

        assert stats.available_permits == 7

    def test_utilization(self) -> None:
        """Test utilization calculation."""
        stats = BulkheadStats(
            name="test", max_concurrent=10, current_concurrent=5
        )

        assert stats.utilization == 0.5

    def test_utilization_zero_max(self) -> None:
        """Test utilization with zero max concurrent."""
        stats = BulkheadStats(
            name="test", max_concurrent=0, current_concurrent=0
        )

        assert stats.utilization == 0.0

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        stats = BulkheadStats(
            name="test",
            max_concurrent=10,
            total_completed=8,
            total_failed=2,
        )

        assert stats.success_rate == 0.8

    def test_success_rate_no_operations(self) -> None:
        """Test success rate with no operations."""
        stats = BulkheadStats(name="test", max_concurrent=10)

        assert stats.success_rate == 0.0

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        stats = BulkheadStats(
            name="test",
            max_concurrent=10,
            current_concurrent=3,
            total_accepted=100,
            total_rejected=5,
            total_completed=90,
            total_failed=10,
        )

        result = stats.to_dict()

        assert result["name"] == "test"
        assert result["max_concurrent"] == 10
        assert result["current_concurrent"] == 3
        assert result["available_permits"] == 7
        assert result["total_accepted"] == 100
        assert result["total_rejected"] == 5


class TestBulkhead:
    """Tests for Bulkhead class."""

    @pytest.fixture
    def bulkhead_instance(self) -> Bulkhead[str]:
        """Create bulkhead instance."""
        return Bulkhead[str](name="test", max_concurrent=2, max_wait_seconds=0.1)

    def test_init_with_params(self) -> None:
        """Test initialization with parameters."""
        bh = Bulkhead[str](name="test", max_concurrent=5, max_wait_seconds=2.0)

        assert bh.name == "test"
        assert bh._config.max_concurrent == 5

    def test_init_with_config(self) -> None:
        """Test initialization with config object."""
        config = BulkheadConfig(max_concurrent=3, max_wait_seconds=1.0)
        bh = Bulkhead[str](name="test", config=config)

        assert bh._config.max_concurrent == 3

    def test_state_accepting(self, bulkhead_instance: Bulkhead[str]) -> None:
        """Test state is ACCEPTING when permits available."""
        assert bulkhead_instance.state == BulkheadState.ACCEPTING

    def test_stats_property(self, bulkhead_instance: Bulkhead[str]) -> None:
        """Test stats property returns BulkheadStats."""
        stats = bulkhead_instance.stats

        assert isinstance(stats, BulkheadStats)
        assert stats.name == "test"

    @pytest.mark.asyncio
    async def test_acquire_success(self, bulkhead_instance: Bulkhead[str]) -> None:
        """Test successful permit acquisition."""
        result = await bulkhead_instance.acquire()

        assert result is True
        assert bulkhead_instance._current_concurrent == 1

    @pytest.mark.asyncio
    async def test_acquire_timeout(self) -> None:
        """Test permit acquisition timeout."""
        bh = Bulkhead[str](name="test", max_concurrent=1, max_wait_seconds=0.01)

        # Acquire first permit
        await bh.acquire()

        # Second acquire should timeout
        result = await bh.acquire()

        assert result is False
        assert bh.rejected_count == 1

    @pytest.mark.asyncio
    async def test_release(self, bulkhead_instance: Bulkhead[str]) -> None:
        """Test permit release."""
        await bulkhead_instance.acquire()
        assert bulkhead_instance._current_concurrent == 1

        await bulkhead_instance.release()

        assert bulkhead_instance._current_concurrent == 0

    @pytest.mark.asyncio
    async def test_release_without_acquire(
        self, bulkhead_instance: Bulkhead[str]
    ) -> None:
        """Test release without prior acquire does nothing."""
        await bulkhead_instance.release()

        assert bulkhead_instance._current_concurrent == 0

    @pytest.mark.asyncio
    async def test_acquire_context_success(
        self, bulkhead_instance: Bulkhead[str]
    ) -> None:
        """Test acquire context manager success."""
        async with bulkhead_instance.acquire_context():
            assert bulkhead_instance._current_concurrent == 1

        assert bulkhead_instance._current_concurrent == 0
        assert bulkhead_instance._completed_count == 1

    @pytest.mark.asyncio
    async def test_acquire_context_failure(
        self, bulkhead_instance: Bulkhead[str]
    ) -> None:
        """Test acquire context manager with exception."""
        with pytest.raises(ValueError):
            async with bulkhead_instance.acquire_context():
                raise ValueError("test error")

        assert bulkhead_instance._current_concurrent == 0
        assert bulkhead_instance._failed_count == 1

    @pytest.mark.asyncio
    async def test_acquire_context_rejected(self) -> None:
        """Test acquire context manager when rejected."""
        bh = Bulkhead[str](name="test", max_concurrent=1, max_wait_seconds=0.01)
        await bh.acquire()

        with pytest.raises(BulkheadRejectedError):
            async with bh.acquire_context():
                pass

    @pytest.mark.asyncio
    async def test_execute(self, bulkhead_instance: Bulkhead[str]) -> None:
        """Test execute method."""

        async def operation() -> str:
            return "result"

        result = await bulkhead_instance.execute(operation)

        assert result == "result"

    @pytest.mark.asyncio
    async def test_execute_with_args(self, bulkhead_instance: Bulkhead[str]) -> None:
        """Test execute method with arguments."""

        async def operation(a: int, b: int) -> int:
            return a + b

        result = await bulkhead_instance.execute(operation, 1, 2)

        assert result == 3

    @pytest.mark.asyncio
    async def test_execute_safe_success(
        self, bulkhead_instance: Bulkhead[str]
    ) -> None:
        """Test execute_safe returns Ok on success."""

        async def operation() -> str:
            return "result"

        result = await bulkhead_instance.execute_safe(operation)

        assert result.is_ok()
        assert result.unwrap() == "result"

    @pytest.mark.asyncio
    async def test_execute_safe_failure(
        self, bulkhead_instance: Bulkhead[str]
    ) -> None:
        """Test execute_safe returns Err on failure."""

        async def operation() -> str:
            raise ValueError("test error")

        result = await bulkhead_instance.execute_safe(operation)

        assert result.is_err()


class TestBulkheadRegistry:
    """Tests for BulkheadRegistry."""

    @pytest.fixture
    def registry(self) -> BulkheadRegistry:
        """Create registry instance."""
        return BulkheadRegistry()

    def test_register(self, registry: BulkheadRegistry) -> None:
        """Test registering a bulkhead."""
        bh = registry.register("test", max_concurrent=5)

        assert bh.name == "test"
        assert registry.get("test") is bh

    def test_get_missing(self, registry: BulkheadRegistry) -> None:
        """Test getting missing bulkhead returns None."""
        result = registry.get("missing")

        assert result is None

    def test_get_or_create_new(self, registry: BulkheadRegistry) -> None:
        """Test get_or_create creates new bulkhead."""
        bh = registry.get_or_create("test", max_concurrent=5)

        assert bh.name == "test"
        assert registry.get("test") is bh

    def test_get_or_create_existing(self, registry: BulkheadRegistry) -> None:
        """Test get_or_create returns existing bulkhead."""
        bh1 = registry.register("test", max_concurrent=5)
        bh2 = registry.get_or_create("test", max_concurrent=10)

        assert bh1 is bh2

    def test_list_names(self, registry: BulkheadRegistry) -> None:
        """Test listing bulkhead names."""
        registry.register("bh1")
        registry.register("bh2")

        names = registry.list_names()

        assert "bh1" in names
        assert "bh2" in names

    def test_get_all_stats(self, registry: BulkheadRegistry) -> None:
        """Test getting all stats."""
        registry.register("bh1")
        registry.register("bh2")

        stats = registry.get_all_stats()

        assert "bh1" in stats
        assert "bh2" in stats
        assert isinstance(stats["bh1"], BulkheadStats)


class TestBulkheadDecorator:
    """Tests for bulkhead decorator."""

    @pytest.mark.asyncio
    async def test_decorator_basic(self) -> None:
        """Test basic decorator usage."""

        @bulkhead("test", max_concurrent=2)
        async def operation() -> str:
            return "result"

        result = await operation()

        assert result == "result"

    @pytest.mark.asyncio
    async def test_decorator_with_args(self) -> None:
        """Test decorator with function arguments."""

        @bulkhead("test", max_concurrent=2)
        async def operation(a: int, b: int) -> int:
            return a + b

        result = await operation(1, 2)

        assert result == 3

    @pytest.mark.asyncio
    async def test_decorator_with_registry(self) -> None:
        """Test decorator with custom registry."""
        registry = BulkheadRegistry()

        @bulkhead("test", max_concurrent=2, registry=registry)
        async def operation() -> str:
            return "result"

        await operation()

        assert registry.get("test") is not None
