"""Unit tests for correlation ID management.

Tests correlation ID context variable management.
"""

import pytest

from core.shared.logging.correlation import (
    clear_correlation_id,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
)


class TestGenerateCorrelationId:
    """Tests for generate_correlation_id function."""

    def test_returns_string(self) -> None:
        cid = generate_correlation_id()
        assert isinstance(cid, str)

    def test_uuid_format(self) -> None:
        cid = generate_correlation_id()
        assert len(cid) == 36
        assert cid.count("-") == 4

    def test_unique_ids(self) -> None:
        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestCorrelationIdContext:
    """Tests for correlation ID context management."""

    def setup_method(self) -> None:
        """Clear correlation ID before each test."""
        clear_correlation_id()

    def teardown_method(self) -> None:
        """Clear correlation ID after each test."""
        clear_correlation_id()

    def test_get_returns_none_when_not_set(self) -> None:
        assert get_correlation_id() is None

    def test_set_and_get(self) -> None:
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

    def test_set_generates_id_when_none(self) -> None:
        cid = set_correlation_id()
        assert cid is not None
        assert len(cid) == 36
        assert get_correlation_id() == cid

    def test_set_uses_provided_id(self) -> None:
        cid = set_correlation_id("custom-id")
        assert cid == "custom-id"
        assert get_correlation_id() == "custom-id"

    def test_clear_removes_id(self) -> None:
        set_correlation_id("test-123")
        clear_correlation_id()
        assert get_correlation_id() is None

    def test_overwrite_existing(self) -> None:
        set_correlation_id("first")
        set_correlation_id("second")
        assert get_correlation_id() == "second"


class TestCorrelationIdIsolation:
    """Tests for correlation ID isolation between contexts."""

    def setup_method(self) -> None:
        clear_correlation_id()

    def teardown_method(self) -> None:
        clear_correlation_id()

    @pytest.mark.asyncio
    async def test_async_context_isolation(self) -> None:
        """Test that correlation IDs are isolated in async contexts."""
        import asyncio

        results = []

        async def task(task_id: str) -> None:
            set_correlation_id(f"task-{task_id}")
            await asyncio.sleep(0.01)
            results.append((task_id, get_correlation_id()))

        await asyncio.gather(
            task("1"),
            task("2"),
            task("3"),
        )

        # Each task should have its own correlation ID
        for task_id, cid in results:
            assert cid == f"task-{task_id}"
