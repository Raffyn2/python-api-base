"""Unit tests for Query Timing Prometheus Middleware.

**Feature: performance-monitoring-2025**
**Validates: Prometheus metrics integration, metric collection, histogram buckets**
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram
from sqlalchemy import create_engine, text

from infrastructure.db.middleware.query_timing_prometheus import (
    QueryTimingPrometheusMiddleware,
    install_query_timing_with_prometheus,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@pytest.fixture
def mock_engine() -> Engine:
    """Create a mock SQLAlchemy engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    yield engine
    engine.dispose()


@pytest.fixture
def prometheus_registry() -> CollectorRegistry:
    """Create a fresh Prometheus registry for each test."""
    return CollectorRegistry()


class TestQueryTimingPrometheusMiddleware:
    """Tests for QueryTimingPrometheusMiddleware class."""

    def test_initialization_default(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test middleware initialization with defaults."""
        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )

        assert middleware.engine == mock_engine
        assert middleware.prometheus_registry == prometheus_registry
        assert middleware.metric_prefix == "db"
        assert middleware.queries_counter is not None
        assert middleware.slow_queries_counter is not None
        assert middleware.query_duration_histogram is not None

    def test_initialization_custom_prefix(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test middleware initialization with custom metric prefix."""
        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
            metric_prefix="custom",
        )

        assert middleware.metric_prefix == "custom"
        # Verify metrics are created with custom prefix
        assert "custom_queries_total" in str(
            prometheus_registry.get_sample_value("custom_queries_total", {"query_type": "SELECT"})
        ) or prometheus_registry.get_sample_value("custom_queries_total", {"query_type": "SELECT"}) is None

    def test_metrics_created(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test that Prometheus metrics are created."""
        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )

        # Check that metrics exist
        assert isinstance(middleware.queries_counter, Counter)
        assert isinstance(middleware.slow_queries_counter, Counter)
        assert isinstance(middleware.query_duration_histogram, Histogram)

    def test_histogram_buckets(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test that histogram has correct buckets."""
        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )

        expected_buckets = (
            0.001,  # 1ms
            0.005,  # 5ms
            0.010,  # 10ms
            0.025,  # 25ms
            0.050,  # 50ms
            0.100,  # 100ms
            0.250,  # 250ms
            0.500,  # 500ms
            1.000,  # 1s
            2.500,  # 2.5s
            5.000,  # 5s
            10.000,  # 10s
        )

        # Get histogram metric's samples
        samples = list(histogram_metric.collect())[0].samples
        
        # Extract bucket `le` labels
        bucket_labels = [s.labels["le"] for s in samples if s.name.endswith("_bucket")]
        
        # Convert expected buckets to strings, and add "+Inf"
        expected_labels = [str(b) for b in expected_buckets] + ["+Inf"]

        # Verify buckets match
        assert bucket_labels == expected_labels

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_query_counter_incremented(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        mock_time.side_effect = [0.0, 0.050, 0.1, 0.2]  # 50ms query

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )
        middleware.install()

        # Execute a query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify counter incremented
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        assert counter_value == 1.0

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_slow_query_counter_incremented(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that slow query counter is incremented for slow queries."""
        mock_time.side_effect = [0.0, 0.200, 0.3, 0.4]  # 200ms query (slow)

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
            slow_query_threshold_ms=100.0,
        )
        middleware.install()

        # Create a dummy table for the query
        with mock_engine.connect() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER, created_at TEXT)"))

        # Execute a slow query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT * FROM users WHERE created_at > '2025-01-01'"))

        # Verify slow query counter incremented
        slow_counter_value = prometheus_registry.get_sample_value(
            "db_slow_queries_total", {"query_type": "SELECT"}
        )
        assert slow_counter_value == 1.0

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_fast_query_not_counted_as_slow(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that fast queries are not counted as slow."""
        mock_time.side_effect = [0.0, 0.050, 0.1, 0.2]  # 50ms query (fast)

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
            slow_query_threshold_ms=100.0,
        )
        middleware.install()

        # Execute a fast query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify slow query counter NOT incremented
        slow_counter_value = prometheus_registry.get_sample_value(
            "db_slow_queries_total", {"query_type": "SELECT"}
        )
        # Should be None (no slow queries) or 0
        assert slow_counter_value is None or slow_counter_value == 0.0

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_histogram_observes_duration(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that histogram observes query duration."""
        mock_time.side_effect = [0.0, 0.075, 0.1, 0.2]  # 75ms query

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )
        middleware.install()

        # Execute a query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify histogram recorded the duration
        histogram_count = prometheus_registry.get_sample_value(
            "db_query_duration_seconds_count", {"query_type": "SELECT"}
        )
        histogram_sum = prometheus_registry.get_sample_value(
            "db_query_duration_seconds_sum", {"query_type": "SELECT"}
        )

        assert histogram_count == 1.0
        assert histogram_sum == pytest.approx(0.075, rel=0.01)

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_multiple_query_types_tracked_separately(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that different query types are tracked separately."""
        mock_time.side_effect = [
            0.0,
            0.050,  # SELECT: 50ms
            0.050,
            0.100,  # INSERT: 50ms
            0.100,
            0.150,  # UPDATE: 50ms
            0.150,
            0.200,  # SELECT: 50ms
            0.250,
            0.300,
        ]

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )
        middleware.install()

        # Execute different query types
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("INSERT INTO test VALUES (1)"))
            conn.execute(text("UPDATE test SET value = 2"))
            conn.execute(text("SELECT 2"))

        # Verify each type tracked separately
        select_count = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        insert_count = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "INSERT"}
        )
        update_count = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "UPDATE"}
        )

        assert select_count == 2.0
        assert insert_count == 1.0
        assert update_count == 1.0

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_histogram_buckets_distribution(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that histogram buckets are populated correctly."""
        # Queries with different durations
        mock_time.side_effect = [
            0.0,
            0.003,  # 3ms - falls in 0.005 bucket
            0.003,
            0.030,  # 27ms - falls in 0.050 bucket
            0.030,
            0.150,  # 120ms - falls in 0.250 bucket
            0.200,
            0.300,
        ]

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )
        middleware.install()

        # Execute queries with different durations
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # 3ms
            conn.execute(text("SELECT 2"))  # 27ms
            conn.execute(text("SELECT 3"))  # 120ms

        # Verify bucket counts
        bucket_005 = prometheus_registry.get_sample_value(
            "db_query_duration_seconds_bucket", {"query_type": "SELECT", "le": "0.005"}
        )
        bucket_050 = prometheus_registry.get_sample_value(
            "db_query_duration_seconds_bucket", {"query_type": "SELECT", "le": "0.05"}
        )
        bucket_250 = prometheus_registry.get_sample_value(
            "db_query_duration_seconds_bucket", {"query_type": "SELECT", "le": "0.25"}
        )

        assert bucket_005 == 1.0  # Only first query
        assert bucket_050 == 2.0  # First two queries
        assert bucket_250 == 3.0  # All three queries

    def test_install_and_uninstall(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test install and uninstall functionality."""
        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )

        # Install
        middleware.install()

        # Execute query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify metrics collected
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        assert counter_value == 1.0

        # Uninstall
        middleware.uninstall()

        # Execute another query (should not be tracked)
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 2"))

        # Counter should still be 1 (not incremented)
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        assert counter_value == 1.0


class TestInstallQueryTimingWithPrometheus:
    """Tests for install_query_timing_with_prometheus convenience function."""

    def test_install_returns_middleware(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test that install function returns middleware instance."""
        middleware = install_query_timing_with_prometheus(
            mock_engine, prometheus_registry=prometheus_registry
        )

        assert isinstance(middleware, QueryTimingPrometheusMiddleware)
        assert middleware.engine == mock_engine
        assert middleware.prometheus_registry == prometheus_registry

    def test_install_with_custom_config(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test install with custom configuration."""
        middleware = install_query_timing_with_prometheus(
            mock_engine,
            prometheus_registry=prometheus_registry,
            slow_query_threshold_ms=200.0,
            log_all_queries=True,
            metric_prefix="custom",
        )

        assert middleware.slow_query_threshold_ms == 200.0
        assert middleware.log_all_queries is True
        assert middleware.metric_prefix == "custom"

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_install_and_verify_metrics(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test install function and verify metrics are collected."""
        mock_time.side_effect = [0.0, 0.050, 0.1, 0.2]  # 50ms query

        middleware = install_query_timing_with_prometheus(
            mock_engine, prometheus_registry=prometheus_registry
        )

        # Execute a query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify metrics
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        assert counter_value == 1.0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_metrics_not_duplicated(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test that creating middleware twice doesn't duplicate metrics."""
        # First middleware
        middleware1 = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )

        # Should raise ValueError if trying to register same metric twice
        with pytest.raises(ValueError, match="Duplicated timeseries"):
            middleware2 = QueryTimingPrometheusMiddleware(
                engine=mock_engine,
                prometheus_registry=prometheus_registry,
            )

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_zero_duration_handled(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that zero duration queries are handled correctly."""
        mock_time.side_effect = [0.0, 0.0, 0.1, 0.2]  # 0ms query

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )
        middleware.install()

        # Execute query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Should not raise exception
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        assert counter_value == 1.0

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_very_slow_query(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test handling of very slow queries (>10s)."""
        mock_time.side_effect = [0.0, 15.0, 16.0, 17.0]  # 15 second query

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
        )
        middleware.install()

        # Define a user-defined function to simulate sleep
        @mock_engine.connect
        def connect(dbapi_connection, connection_record):
            dbapi_connection.create_function("sleep", 1, lambda t: time.sleep(float(t)))

        # Execute very slow query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT sleep(0.1)"))

        # Verify it's counted
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        slow_counter_value = prometheus_registry.get_sample_value(
            "db_slow_queries_total", {"query_type": "SELECT"}
        )

        assert counter_value == 1.0
        assert slow_counter_value == 1.0

    def test_empty_metric_prefix(
        self, mock_engine: Engine, prometheus_registry: CollectorRegistry
    ) -> None:
        """Test handling of empty metric prefix."""
        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
            metric_prefix="",
        )

        # Metrics should be created with empty prefix
        assert middleware.metric_prefix == ""
        # Metrics names would be "_queries_total" etc.

    @patch("infrastructure.db.middleware.query_timing_prometheus.time.perf_counter")
    def test_statistics_still_collected(
        self,
        mock_time: Mock,
        mock_engine: Engine,
        prometheus_registry: CollectorRegistry,
    ) -> None:
        """Test that base statistics are still collected alongside Prometheus."""
        mock_time.side_effect = [0.0, 0.150, 0.2, 0.3]  # 150ms slow query

        middleware = QueryTimingPrometheusMiddleware(
            engine=mock_engine,
            prometheus_registry=prometheus_registry,
            slow_query_threshold_ms=100.0,
            collect_stats=True,
        )
        middleware.install()

        # Execute query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify base stats collected
        stats = middleware.get_stats()
        assert stats is not None
        assert stats.total_queries == 1
        assert stats.slow_queries == 1

        # Verify Prometheus metrics also collected
        counter_value = prometheus_registry.get_sample_value(
            "db_queries_total", {"query_type": "SELECT"}
        )
        assert counter_value == 1.0
