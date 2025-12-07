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
