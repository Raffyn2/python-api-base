"""Unit tests for infrastructure/resilience/bulkhead.py.

Tests bulkhead isolation pattern.

**Task 20.3: Create tests for bulkhead.py**
**Requirements: 4.3**
"""

import asyncio

import pytest

from infrastructure.resilience.bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadRegistry,
    BulkheadRejectedError,
    BulkheadState,
    BulkheadStats,
)


class TestBulkheadConfig:
    """Tests for BulkheadConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BulkheadConfig()

        assert config.max_concurrent == 10
        assert config.max_wait_seconds == 5.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BulkheadConfig(max_concurrent=5, max_wait_seconds=1.0)

        assert config.max_concurrent == 5
        assert config.max_wait_seconds == 1.0


class TestBulkheadStats:
    """Tests for BulkheadStats."""

    def test_available_permits(self) -> None:
        """Test available_permits calculation."""
        stats = BulkheadStats(
            name="test",
            max_concurrent=10,
            current_concurrent=3,
        )

        assert stats.available_permits == 7

    def test_utilization(self) -> None:
        """Test utilization calculation."""
        stats = BulkheadStats(
            name="test",
            max_concurrent=10,
            current_concurrent=5,
        )

        assert stats.utilization == 0.5

    def test_success_rate(self) -> None:
        """Test success_rate calculation."""
        stats = BulkheadStats(
            name="test",
            max_concurrent=10,
            total_completed=8,
            total_failed=2,
        )

        assert stats.success_rate == 0.8

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        stats = BulkheadStats(name="test", max_concurrent=10)
        result = stats.to_dict()

        assert result["name"] == "test"
        assert result["max_concurrent"] == 10


class TestBulkhead:
    """Tests for Bulkhead class."""

    @pytest.mark.asyncio
    async def test_allows_within_limit(self) -> None:
        """Test bulkhead allows calls within limit."""
        bulkhead = Bulkhead[str](name="test", max_concurrent=2)

        async def task() -> str:
            await asyncio.sleep(0.01)
            return "done"

        result = await bulkhead.execute(task)

        assert result == "done"

    @pytest.mark.asyncio
    async def test_rejects_when_full(self) -> None:
        """Test bulkhead rejects when full."""
        bulkhead = Bulkhead[str](name="test", max_concurrent=1, max_wait_seconds=0.01)

        async def slow_task() -> str:
            await asyncio.sleep(0.5)
            return "done"

        # Start first task
        task1 = asyncio.create_task(bulkhead.execute(slow_task))
        await asyncio.sleep(0.02)  # Let it acquire semaphore

        # Second task should be rejected
        with pytest.raises(BulkheadRejectedError):
            await bulkhead.execute(slow_task)

        task1.cancel()
        try:
            await task1
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_concurrent_limit_respected(self) -> None:
        """Test concurrent limit is respected."""
        bulkhead = Bulkhead[None](name="test", max_concurrent=3)
        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrent() -> None:
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1

        tasks = [bulkhead.execute(track_concurrent) for _ in range(5)]
        await asyncio.gather(*tasks)

        assert max_concurrent <= 3

    def test_state_property(self) -> None:
        """Test state property."""
        bulkhead = Bulkhead[str](name="test", max_concurrent=2)

        assert bulkhead.state == BulkheadState.ACCEPTING

    def test_stats_property(self) -> None:
        """Test stats property."""
        bulkhead = Bulkhead[str](name="test", max_concurrent=5)
        stats = bulkhead.stats

        assert stats.name == "test"
        assert stats.max_concurrent == 5


class TestBulkheadRegistry:
    """Tests for BulkheadRegistry."""

    def test_register(self) -> None:
        """Test registering a bulkhead."""
        registry = BulkheadRegistry()

        bulkhead = registry.register("test", max_concurrent=5)

        assert bulkhead.name == "test"

    def test_get(self) -> None:
        """Test getting a bulkhead."""
        registry = BulkheadRegistry()
        registry.register("test")

        bulkhead = registry.get("test")

        assert bulkhead is not None

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent bulkhead."""
        registry = BulkheadRegistry()

        bulkhead = registry.get("nonexistent")

        assert bulkhead is None

    def test_get_or_create(self) -> None:
        """Test get_or_create."""
        registry = BulkheadRegistry()

        bh1 = registry.get_or_create("test")
        bh2 = registry.get_or_create("test")

        assert bh1 is bh2

    def test_list_names(self) -> None:
        """Test listing bulkhead names."""
        registry = BulkheadRegistry()
        registry.register("bh1")
        registry.register("bh2")

        names = registry.list_names()

        assert "bh1" in names
        assert "bh2" in names
