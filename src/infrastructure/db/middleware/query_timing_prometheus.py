"""Query timing middleware with Prometheus metrics integration.

Extends QueryTimingMiddleware with Prometheus metrics collection.

**Feature: performance-monitoring-2025**
**Validates: Next Steps - Prometheus Integration**
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from prometheus_client import Counter, Histogram

from infrastructure.db.middleware.query_timing import (
    QueryStats,
    QueryTimingMiddleware,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger(__name__)


class QueryTimingPrometheusMiddleware(QueryTimingMiddleware):
    """Query timing middleware with Prometheus metrics.

    Extends base QueryTimingMiddleware to export metrics to Prometheus.

    Metrics exported:
    - db_queries_total: Total number of queries by type
    - db_slow_queries_total: Total number of slow queries by type
    - db_query_duration_seconds: Query duration histogram by type

    Example:
        >>> from sqlalchemy import create_engine
        >>> from infrastructure.prometheus import get_registry
        >>> engine = create_engine("postgresql://...")
        >>> middleware = QueryTimingPrometheusMiddleware(
        ...     engine=engine,
        ...     slow_query_threshold_ms=100.0,
        ...     prometheus_registry=get_registry(),
        ... )
        >>> middleware.install()
        >>> # Metrics are now exported at /metrics endpoint
    """

    def __init__(
        self,
        engine: Engine,
        slow_query_threshold_ms: float = 100.0,
        log_all_queries: bool = False,
        collect_stats: bool = True,
        prometheus_registry: Any = None,
        metric_prefix: str = "db",
    ):
        """Initialize Prometheus-enabled query timing middleware.

        Args:
            engine: SQLAlchemy engine
            slow_query_threshold_ms: Threshold to consider a query slow (milliseconds)
            log_all_queries: If True, log all queries (not just slow ones)
            collect_stats: If True, collect query statistics
            prometheus_registry: Prometheus registry (defaults to default registry)
            metric_prefix: Prefix for metric names (default: "db")
        """
        super().__init__(
            engine=engine,
            slow_query_threshold_ms=slow_query_threshold_ms,
            log_all_queries=log_all_queries,
            collect_stats=collect_stats,
        )

        self.prometheus_registry = prometheus_registry
        self.metric_prefix = metric_prefix

        # Initialize Prometheus metrics
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        # Counter for total queries
        self.queries_counter = Counter(
            name=f"{self.metric_prefix}_queries_total",
            documentation="Total number of database queries by type",
            labelnames=["query_type"],
            registry=self.prometheus_registry,
        )

        # Counter for slow queries
        self.slow_queries_counter = Counter(
            name=f"{self.metric_prefix}_slow_queries_total",
            documentation="Total number of slow database queries by type",
            labelnames=["query_type"],
            registry=self.prometheus_registry,
        )

        # Histogram for query duration
        self.query_duration_histogram = Histogram(
            name=f"{self.metric_prefix}_query_duration_seconds",
            documentation="Database query duration in seconds",
            labelnames=["query_type"],
            buckets=(
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
            ),
            registry=self.prometheus_registry,
        )

        logger.info(
            "Prometheus metrics initialized for query timing",
            extra={
                "metric_prefix": self.metric_prefix,
                "metrics": [
                    f"{self.metric_prefix}_queries_total",
                    f"{self.metric_prefix}_slow_queries_total",
                    f"{self.metric_prefix}_query_duration_seconds",
                ],
            },
        )

    def _after_cursor_execute(
        self,
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Event handler after query execution with Prometheus metrics.

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: If True, multiple parameters were executed
        """
        # Call parent implementation for logging and stats
        super()._after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        )

        # Calculate duration
        start_time = getattr(context, "_query_start_time", None)
        if start_time is None:
            return

        duration_s = time.perf_counter() - start_time
        duration_ms = duration_s * 1000

        # Get query type
        query_type = QueryStats._get_query_type(statement)

        # Update Prometheus metrics
        try:
            # Increment queries counter
            self.queries_counter.labels(query_type=query_type).inc()

            # Record duration in histogram
            self.query_duration_histogram.labels(query_type=query_type).observe(
                duration_s
            )

            # Increment slow queries counter if applicable
            if duration_ms >= self.slow_query_threshold_ms:
                self.slow_queries_counter.labels(query_type=query_type).inc()

        except Exception as e:
            logger.error(
                "Failed to update Prometheus metrics",
                extra={"error": str(e), "query_type": query_type},
            )


def install_query_timing_with_prometheus(
    engine: Engine,
    slow_query_threshold_ms: float = 100.0,
    log_all_queries: bool = False,
    collect_stats: bool = True,
    prometheus_registry: Any = None,
    metric_prefix: str = "db",
) -> QueryTimingPrometheusMiddleware:
    """Install query timing middleware with Prometheus metrics.

    This is a convenience function that creates and installs the middleware
    with Prometheus integration.

    Args:
        engine: SQLAlchemy engine
        slow_query_threshold_ms: Threshold to consider a query slow (milliseconds)
        log_all_queries: If True, log all queries (not just slow ones)
        collect_stats: If True, collect query statistics
        prometheus_registry: Prometheus registry (defaults to default registry)
        metric_prefix: Prefix for metric names (default: "db")

    Returns:
        Installed QueryTimingPrometheusMiddleware instance

    Example:
        >>> from sqlalchemy import create_engine
        >>> from infrastructure.prometheus import get_registry
        >>> engine = create_engine("postgresql://...")
        >>> middleware = install_query_timing_with_prometheus(
        ...     engine,
        ...     slow_query_threshold_ms=100.0,
        ...     prometheus_registry=get_registry(),
        ... )
        >>> # Later, view metrics at /metrics endpoint
        >>> # - db_queries_total{query_type="SELECT"} 1234
        >>> # - db_slow_queries_total{query_type="SELECT"} 56
        >>> # - db_query_duration_seconds_bucket{query_type="SELECT",le="0.1"} 1000
    """
    middleware = QueryTimingPrometheusMiddleware(
        engine=engine,
        slow_query_threshold_ms=slow_query_threshold_ms,
        log_all_queries=log_all_queries,
        collect_stats=collect_stats,
        prometheus_registry=prometheus_registry,
        metric_prefix=metric_prefix,
    )
    middleware.install()
    return middleware


__all__ = [
    "QueryTimingPrometheusMiddleware",
    "install_query_timing_with_prometheus",
]
