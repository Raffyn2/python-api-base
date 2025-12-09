"""Tests for observability metrics module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.3**
"""

import pytest

from infrastructure.observability.metrics import (
    CacheMetrics,
    CacheMetricsDict,
    CacheMetricsExporter,
)


class TestCacheMetrics:
    """Tests for CacheMetrics."""

    def test_default_values(self) -> None:
        """Test default metric values."""
        metrics = CacheMetrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.evictions == 0

    def test_record_hit(self) -> None:
        """Test recording a cache hit."""
        metrics = CacheMetrics()
        metrics.record_hit()
        assert metrics.hits == 1

    def test_record_multiple_hits(self) -> None:
        """Test recording multiple cache hits."""
        metrics = CacheMetrics()
        for _ in range(5):
            metrics.record_hit()
        assert metrics.hits == 5

    def test_record_miss(self) -> None:
        """Test recording a cache miss."""
        metrics = CacheMetrics()
        metrics.record_miss()
        assert metrics.misses == 1

    def test_record_multiple_misses(self) -> None:
        """Test recording multiple cache misses."""
        metrics = CacheMetrics()
        for _ in range(3):
            metrics.record_miss()
        assert metrics.misses == 3

    def test_record_eviction(self) -> None:
        """Test recording a cache eviction."""
        metrics = CacheMetrics()
        metrics.record_eviction()
        assert metrics.evictions == 1

    def test_hit_rate_no_requests(self) -> None:
        """Test hit rate with no requests."""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0

    def test_hit_rate_all_hits(self) -> None:
        """Test hit rate with all hits."""
        metrics = CacheMetrics()
        for _ in range(10):
            metrics.record_hit()
        assert metrics.hit_rate == 1.0

    def test_hit_rate_all_misses(self) -> None:
        """Test hit rate with all misses."""
        metrics = CacheMetrics()
        for _ in range(10):
            metrics.record_miss()
        assert metrics.hit_rate == 0.0

    def test_hit_rate_mixed(self) -> None:
        """Test hit rate with mixed hits and misses."""
        metrics = CacheMetrics()
        for _ in range(7):
            metrics.record_hit()
        for _ in range(3):
            metrics.record_miss()
        assert metrics.hit_rate == 0.7

    def test_total_requests(self) -> None:
        """Test total requests calculation."""
        metrics = CacheMetrics()
        for _ in range(5):
            metrics.record_hit()
        for _ in range(3):
            metrics.record_miss()
        assert metrics.total_requests == 8

    def test_reset(self) -> None:
        """Test resetting metrics."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_miss()
        metrics.record_eviction()
        metrics.reset()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.evictions == 0

    def test_to_dict(self) -> None:
        """Test converting metrics to dictionary."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()
        metrics.record_eviction()

        result = metrics.to_dict()

        assert result["hits"] == 2
        assert result["misses"] == 1
        assert result["evictions"] == 1
        assert result["total_requests"] == 3
        assert abs(result["hit_rate"] - 0.6667) < 0.01

    def test_to_dict_type(self) -> None:
        """Test that to_dict returns correct type."""
        metrics = CacheMetrics()
        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert "hits" in result
        assert "misses" in result
        assert "evictions" in result
        assert "hit_rate" in result
        assert "total_requests" in result


class TestCacheMetricsExporter:
    """Tests for CacheMetricsExporter."""

    def test_create_with_defaults(self) -> None:
        """Test creating exporter with defaults."""
        exporter = CacheMetricsExporter()
        assert exporter._cache_name == "default"
        assert exporter._meter_name == "my_app.cache"

    def test_create_with_custom_name(self) -> None:
        """Test creating exporter with custom cache name."""
        exporter = CacheMetricsExporter(cache_name="user_cache")
        assert exporter._cache_name == "user_cache"

    def test_create_with_custom_meter_name(self) -> None:
        """Test creating exporter with custom meter name."""
        exporter = CacheMetricsExporter(meter_name="custom.meter")
        assert exporter._meter_name == "custom.meter"

    def test_export_metrics_no_otel(self) -> None:
        """Test exporting metrics without OpenTelemetry."""
        exporter = CacheMetricsExporter()
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_miss()

        # Should not raise even without OpenTelemetry
        exporter.export_metrics(metrics)

    def test_export_metrics_tracks_deltas(self) -> None:
        """Test that exporter tracks metric deltas."""
        exporter = CacheMetricsExporter()
        metrics = CacheMetrics()

        # First export
        metrics.record_hit()
        exporter.export_metrics(metrics)
        assert exporter._last_hits == 1

        # Second export with more hits
        metrics.record_hit()
        metrics.record_hit()
        exporter.export_metrics(metrics)
        assert exporter._last_hits == 3

    def test_export_metrics_tracks_misses(self) -> None:
        """Test that exporter tracks miss deltas."""
        exporter = CacheMetricsExporter()
        metrics = CacheMetrics()

        metrics.record_miss()
        exporter.export_metrics(metrics)
        assert exporter._last_misses == 1

    def test_export_metrics_tracks_evictions(self) -> None:
        """Test that exporter tracks eviction deltas."""
        exporter = CacheMetricsExporter()
        metrics = CacheMetrics()

        metrics.record_eviction()
        exporter.export_metrics(metrics)
        assert exporter._last_evictions == 1


class TestMetricsAwareCacheWrapper:
    """Tests for MetricsAwareCacheWrapper."""

    @pytest.fixture
    def mock_provider(self) -> "MockCacheProvider":
        """Create a mock cache provider."""
        return MockCacheProvider()

    @pytest.mark.asyncio
    async def test_get_hit_records_metric(self, mock_provider: "MockCacheProvider") -> None:
        """Test that get records hit when value exists."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        mock_provider.data["key"] = "value"
        wrapper = MetricsAwareCacheWrapper(mock_provider)

        result = await wrapper.get("key")

        assert result == "value"
        assert wrapper.metrics.hits == 1
        assert wrapper.metrics.misses == 0

    @pytest.mark.asyncio
    async def test_get_miss_records_metric(self, mock_provider: "MockCacheProvider") -> None:
        """Test that get records miss when value doesn't exist."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        wrapper = MetricsAwareCacheWrapper(mock_provider)

        result = await wrapper.get("nonexistent")

        assert result is None
        assert wrapper.metrics.hits == 0
        assert wrapper.metrics.misses == 1

    @pytest.mark.asyncio
    async def test_set_stores_value(self, mock_provider: "MockCacheProvider") -> None:
        """Test that set stores value in provider."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        wrapper = MetricsAwareCacheWrapper(mock_provider)

        await wrapper.set("key", "value")

        assert mock_provider.data["key"] == "value"

    @pytest.mark.asyncio
    async def test_delete_removes_value(self, mock_provider: "MockCacheProvider") -> None:
        """Test that delete removes value from provider."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        mock_provider.data["key"] = "value"
        wrapper = MetricsAwareCacheWrapper(mock_provider)

        result = await wrapper.delete("key")

        assert result is True
        assert "key" not in mock_provider.data

    @pytest.mark.asyncio
    async def test_exists_checks_provider(self, mock_provider: "MockCacheProvider") -> None:
        """Test that exists checks provider."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        mock_provider.data["key"] = "value"
        wrapper = MetricsAwareCacheWrapper(mock_provider)

        assert await wrapper.exists("key") is True
        assert await wrapper.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear_clears_provider(self, mock_provider: "MockCacheProvider") -> None:
        """Test that clear clears provider."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        mock_provider.data["key1"] = "value1"
        mock_provider.data["key2"] = "value2"
        wrapper = MetricsAwareCacheWrapper(mock_provider)

        await wrapper.clear()

        assert len(mock_provider.data) == 0

    @pytest.mark.asyncio
    async def test_size_returns_provider_size(self, mock_provider: "MockCacheProvider") -> None:
        """Test that size returns provider size."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        mock_provider.data["key1"] = "value1"
        mock_provider.data["key2"] = "value2"
        wrapper = MetricsAwareCacheWrapper(mock_provider)

        assert await wrapper.size() == 2

    def test_get_metrics_returns_metrics(self, mock_provider: "MockCacheProvider") -> None:
        """Test that get_metrics returns metrics instance."""
        from infrastructure.observability.metrics import MetricsAwareCacheWrapper

        wrapper = MetricsAwareCacheWrapper(mock_provider)
        metrics = wrapper.get_metrics()

        assert metrics is wrapper.metrics

    @pytest.mark.asyncio
    async def test_maybe_export_with_exporter(self, mock_provider: "MockCacheProvider") -> None:
        """Test that metrics are exported at interval."""
        from infrastructure.observability.metrics import (
            CacheMetricsExporter,
            MetricsAwareCacheWrapper,
        )

        exporter = CacheMetricsExporter()
        wrapper = MetricsAwareCacheWrapper(mock_provider, exporter=exporter, export_interval=2)

        # First request - no export
        await wrapper.get("key1")
        assert wrapper._request_count == 1

        # Second request - should export
        await wrapper.get("key2")
        assert wrapper._request_count == 2


class MockCacheProvider:
    """Mock cache provider for testing."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self.data[key] = value

    async def delete(self, key: str) -> bool:
        if key in self.data:
            del self.data[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self.data

    async def clear(self) -> None:
        self.data.clear()

    async def size(self) -> int:
        return len(self.data)
