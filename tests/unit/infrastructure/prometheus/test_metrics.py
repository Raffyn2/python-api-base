"""Unit tests for Prometheus metrics decorators.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements R5.2 - Metrics Decorators**
"""

import pytest

from infrastructure.prometheus.metrics import (
    count_exceptions,
    counter,
    gauge,
    histogram,
    summary,
    timer,
)


class TestCounterDecorator:
    """Tests for counter decorator."""

    def test_sync_counter(self) -> None:
        """Test counter with sync function."""

        @counter("test_sync_counter", "Test counter")
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_counter(self) -> None:
        """Test counter with async function."""

        @counter("test_async_counter", "Test counter")
        async def my_func() -> str:
            return "result"

        result = await my_func()
        assert result == "result"

    def test_counter_with_labels(self) -> None:
        """Test counter with label values."""

        @counter(
            "test_counter_labels",
            "Test counter",
            labels=["endpoint"],
            label_values={"endpoint": "/api"},
        )
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"


class TestGaugeDecorator:
    """Tests for gauge decorator."""

    def test_sync_gauge(self) -> None:
        """Test gauge with sync function."""

        @gauge("test_sync_gauge", "Test gauge")
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_gauge(self) -> None:
        """Test gauge with async function."""

        @gauge("test_async_gauge", "Test gauge")
        async def my_func() -> str:
            return "result"

        result = await my_func()
        assert result == "result"

    def test_gauge_with_labels(self) -> None:
        """Test gauge with label values."""

        @gauge(
            "test_gauge_labels",
            "Test gauge",
            labels=["service"],
            label_values={"service": "api"},
        )
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    def test_gauge_no_track_inprogress(self) -> None:
        """Test gauge without tracking in-progress."""

        @gauge("test_gauge_no_track", "Test gauge", track_inprogress=False)
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"


class TestHistogramDecorator:
    """Tests for histogram decorator."""

    def test_sync_histogram(self) -> None:
        """Test histogram with sync function."""

        @histogram("test_sync_histogram", "Test histogram")
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_histogram(self) -> None:
        """Test histogram with async function."""

        @histogram("test_async_histogram", "Test histogram")
        async def my_func() -> str:
            return "result"

        result = await my_func()
        assert result == "result"

    def test_histogram_with_labels(self) -> None:
        """Test histogram with label values."""

        @histogram(
            "test_histogram_labels",
            "Test histogram",
            labels=["method"],
            label_values={"method": "GET"},
        )
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    def test_histogram_with_buckets(self) -> None:
        """Test histogram with custom buckets."""

        @histogram(
            "test_histogram_buckets",
            "Test histogram",
            buckets=(0.1, 0.5, 1.0, 5.0),
        )
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"


class TestSummaryDecorator:
    """Tests for summary decorator."""

    def test_sync_summary(self) -> None:
        """Test summary with sync function."""

        @summary("test_sync_summary", "Test summary")
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_summary(self) -> None:
        """Test summary with async function."""

        @summary("test_async_summary", "Test summary")
        async def my_func() -> str:
            return "result"

        result = await my_func()
        assert result == "result"

    def test_summary_with_labels(self) -> None:
        """Test summary with label values."""

        @summary(
            "test_summary_labels",
            "Test summary",
            labels=["status"],
            label_values={"status": "success"},
        )
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"


class TestTimerAlias:
    """Tests for timer alias."""

    def test_timer_is_histogram(self) -> None:
        """Test that timer is an alias for histogram."""
        assert timer is histogram


class TestCountExceptionsDecorator:
    """Tests for count_exceptions decorator."""

    def test_sync_no_exception(self) -> None:
        """Test count_exceptions with no exception."""

        @count_exceptions("test_sync_errors", "Test errors")
        def my_func() -> str:
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_no_exception(self) -> None:
        """Test count_exceptions async with no exception."""

        @count_exceptions("test_async_errors", "Test errors")
        async def my_func() -> str:
            return "result"

        result = await my_func()
        assert result == "result"

    def test_sync_with_exception(self) -> None:
        """Test count_exceptions counts exception."""

        @count_exceptions("test_sync_errors_exc", "Test errors")
        def my_func() -> str:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            my_func()

    @pytest.mark.asyncio
    async def test_async_with_exception(self) -> None:
        """Test count_exceptions async counts exception."""

        @count_exceptions("test_async_errors_exc", "Test errors")
        async def my_func() -> str:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await my_func()

    def test_with_labels(self) -> None:
        """Test count_exceptions with labels."""

        @count_exceptions(
            "test_errors_labels",
            "Test errors",
            labels=["endpoint"],
            label_values={"endpoint": "/api"},
        )
        def my_func() -> str:
            raise RuntimeError("test")

        with pytest.raises(RuntimeError):
            my_func()

    def test_specific_exception_type(self) -> None:
        """Test count_exceptions with specific exception type."""

        @count_exceptions(
            "test_errors_specific",
            "Test errors",
            exception_type=ValueError,
        )
        def my_func(should_raise: bool) -> str:
            if should_raise:
                raise ValueError("test")
            return "result"

        # Should not count RuntimeError
        result = my_func(False)
        assert result == "result"

        # Should count ValueError
        with pytest.raises(ValueError):
            my_func(True)
