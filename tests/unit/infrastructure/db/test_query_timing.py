"""Unit tests for Query Timing Middleware - Fixed version.

**Feature: performance-monitoring-2025**
**Validates: Query timing, statistics collection, slow query detection**
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection

from infrastructure.db.middleware.query_timing import (
    QueryStats,
    QueryTimingMiddleware,
    install_query_timing,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@pytest.fixture
def mock_engine() -> Engine:
    """Create a mock SQLAlchemy engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    # Create test table
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER, value TEXT)"))
        conn.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def query_stats() -> QueryStats:
    """Create a fresh QueryStats instance."""
    return QueryStats()


class TestQueryStats:
    """Tests for QueryStats class."""

    def test_initial_state(self, query_stats: QueryStats) -> None:
        """Test QueryStats initial state."""
        assert query_stats.total_queries == 0
        assert query_stats.slow_queries == 0
        assert query_stats.total_duration_ms == 0.0
        assert query_stats.queries_by_type == {}
        assert query_stats.slowest_queries == []

    def test_add_fast_query(self, query_stats: QueryStats) -> None:
        """Test adding a fast query."""
        statement = "SELECT * FROM users WHERE id = 1"
        duration_ms = 50.0

        query_stats.add_query(statement, duration_ms, slow_threshold_ms=100.0)

        assert query_stats.total_queries == 1
        assert query_stats.slow_queries == 0
        assert query_stats.total_duration_ms == 50.0
        assert query_stats.queries_by_type == {"SELECT": 1}

    def test_add_slow_query(self, query_stats: QueryStats) -> None:
        """Test adding a slow query."""
        statement = "SELECT * FROM orders WHERE created_at > NOW()"
        duration_ms = 250.0

        query_stats.add_query(statement, duration_ms, slow_threshold_ms=100.0)

        assert query_stats.total_queries == 1
        assert query_stats.slow_queries == 1
        assert query_stats.total_duration_ms == 250.0
        assert len(query_stats.slowest_queries) == 1
        assert query_stats.slowest_queries[0][1] == 250.0

    def test_multiple_query_types(self, query_stats: QueryStats) -> None:
        """Test tracking multiple query types."""
        queries = [
            ("SELECT * FROM users", 50.0),
            ("INSERT INTO users VALUES (1)", 30.0),
            ("UPDATE users SET name = 'test'", 40.0),
            ("DELETE FROM users WHERE id = 1", 20.0),
            ("SELECT * FROM orders", 60.0),
        ]

        for statement, duration in queries:
            query_stats.add_query(statement, duration, slow_threshold_ms=100.0)

        assert query_stats.total_queries == 5
        assert query_stats.queries_by_type == {
            "SELECT": 2,
            "INSERT": 1,
            "UPDATE": 1,
            "DELETE": 1,
        }

    def test_slowest_queries_limit(self, query_stats: QueryStats) -> None:
        """Test that slowest queries list is limited to 10."""
        for i in range(15):
            statement = f"SELECT * FROM table_{i}"
            duration_ms = float(i * 10)
            query_stats.add_query(statement, duration_ms, slow_threshold_ms=50.0)

        assert len(query_stats.slowest_queries) == 10
        # Should keep the 10 slowest (140, 130, 120, ..., 50)
        assert query_stats.slowest_queries[0][1] == 140.0
        assert query_stats.slowest_queries[-1][1] == 50.0

    def test_get_summary(self, query_stats: QueryStats) -> None:
        """Test get_summary method."""
        queries = [
            ("SELECT * FROM users", 50.0),
            ("SELECT * FROM orders", 150.0),
            ("INSERT INTO logs VALUES (1)", 30.0),
        ]

        for statement, duration in queries:
            query_stats.add_query(statement, duration, slow_threshold_ms=100.0)

        summary = query_stats.get_summary()

        assert summary["total_queries"] == 3
        assert summary["slow_queries"] == 1
        assert summary["total_duration_ms"] == 230.0
        assert summary["average_duration_ms"] == pytest.approx(76.67, rel=0.01)
        assert summary["queries_by_type"] == {"SELECT": 2, "INSERT": 1}
        assert len(summary["slowest_queries"]) == 1

    def test_get_query_type(self) -> None:
        """Test _get_query_type static method."""
        assert QueryStats._get_query_type("SELECT * FROM users") == "SELECT"
        assert QueryStats._get_query_type("  select id from orders  ") == "SELECT"
        assert QueryStats._get_query_type("INSERT INTO users VALUES (1)") == "INSERT"
        assert QueryStats._get_query_type("UPDATE users SET name = 'test'") == "UPDATE"
        assert QueryStats._get_query_type("DELETE FROM users WHERE id = 1") == "DELETE"
        assert QueryStats._get_query_type("BEGIN") == "BEGIN"
        assert QueryStats._get_query_type("COMMIT") == "COMMIT"
        assert QueryStats._get_query_type("ROLLBACK") == "ROLLBACK"
        # CTE queries starting with WITH are classified as OTHER
        assert QueryStats._get_query_type("WITH cte AS (...) SELECT *") == "OTHER"
        assert QueryStats._get_query_type("EXPLAIN SELECT *") == "OTHER"

    def test_get_average_duration(self, query_stats: QueryStats) -> None:
        """Test get_average_duration method."""
        # Empty stats
        assert query_stats.get_average_duration() == 0.0

        # Add some queries
        query_stats.add_query("SELECT 1", 50.0)
        query_stats.add_query("SELECT 2", 100.0)
        query_stats.add_query("SELECT 3", 150.0)

        assert query_stats.get_average_duration() == 100.0


class TestQueryTimingMiddleware:
    """Tests for QueryTimingMiddleware class."""

    def test_initialization_default(self, mock_engine: Engine) -> None:
        """Test middleware initialization with defaults."""
        middleware = QueryTimingMiddleware(engine=mock_engine)

        assert middleware.engine == mock_engine
        assert middleware.slow_query_threshold_ms == 100.0
        assert middleware.log_all_queries is False
        assert middleware.collect_stats is True
        assert middleware.stats is not None
        assert isinstance(middleware.stats, QueryStats)

    def test_initialization_custom(self, mock_engine: Engine) -> None:
        """Test middleware initialization with custom values."""
        middleware = QueryTimingMiddleware(
            engine=mock_engine,
            slow_query_threshold_ms=200.0,
            log_all_queries=True,
            collect_stats=False,
        )

        assert middleware.slow_query_threshold_ms == 200.0
        assert middleware.log_all_queries is True
        assert middleware.collect_stats is False
        assert middleware.stats is None

    def test_install_registers_events(self, mock_engine: Engine) -> None:
        """Test that install registers SQLAlchemy events."""
        middleware = QueryTimingMiddleware(engine=mock_engine)

        # Install middleware
        middleware.install()

        # Check events after installation
        before_events = event.contains(
            mock_engine, "before_cursor_execute", middleware._before_cursor_execute
        )
        after_events = event.contains(
            mock_engine, "after_cursor_execute", middleware._after_cursor_execute
        )

        assert before_events is True
        assert after_events is True

    def test_uninstall_removes_events(self, mock_engine: Engine) -> None:
        """Test that uninstall removes SQLAlchemy events."""
        middleware = QueryTimingMiddleware(engine=mock_engine)
        middleware.install()

        # Uninstall
        middleware.uninstall()

        # Check events removed
        before_events = event.contains(
            mock_engine, "before_cursor_execute", middleware._before_cursor_execute
        )
        after_events = event.contains(
            mock_engine, "after_cursor_execute", middleware._after_cursor_execute
        )

        assert before_events is False
        assert after_events is False

    @patch("infrastructure.db.middleware.query_timing.time.perf_counter")
    @patch("infrastructure.db.middleware.query_timing.logger.log")
    def test_slow_query_logging(
        self, mock_log: Mock, mock_time: Mock, mock_engine: Engine
    ) -> None:
        """Test that slow queries are logged."""
        # Mock time to simulate slow query
        mock_time.side_effect = [0.0, 0.250]  # 250ms query

        middleware = QueryTimingMiddleware(
            engine=mock_engine, slow_query_threshold_ms=100.0
        )
        middleware.install()

        # Execute a query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify log was called
        assert mock_log.called
        # Find the WARNING log call
        warning_calls = [call for call in mock_log.call_args_list if call[0][0] == 30]  # logging.WARNING = 30
        assert len(warning_calls) > 0
        assert "Slow query detected" in str(warning_calls[0])

    @patch("infrastructure.db.middleware.query_timing.time.perf_counter")
    def test_statistics_collection(
        self, mock_time: Mock, mock_engine: Engine
    ) -> None:
        """Test that statistics are collected."""
        mock_time.side_effect = [
            0.0,
            0.050,  # First query: 50ms
            0.050,
            0.200,  # Second query: 150ms
        ]

        middleware = QueryTimingMiddleware(
            engine=mock_engine, slow_query_threshold_ms=100.0, collect_stats=True
        )
        middleware.install()

        # Execute two queries
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("INSERT INTO test VALUES (1, 'test')"))

        # Verify statistics
        stats = middleware.get_stats()
        assert stats.total_queries == 2
        assert stats.slow_queries == 1
        assert stats.queries_by_type == {"SELECT": 1, "INSERT": 1}

    @patch("infrastructure.db.middleware.query_timing.time.perf_counter")
    @patch("infrastructure.db.middleware.query_timing.logger.log")
    def test_log_all_queries(
        self, mock_log: Mock, mock_time: Mock, mock_engine: Engine
    ) -> None:
        """Test that all queries are logged when log_all_queries=True."""
        mock_time.side_effect = [0.0, 0.030]  # 30ms query (fast)

        middleware = QueryTimingMiddleware(
            engine=mock_engine,
            slow_query_threshold_ms=100.0,
            log_all_queries=True,
        )
        middleware.install()

        # Execute a fast query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify log was called with DEBUG level (10)
        assert mock_log.called
        debug_calls = [call for call in mock_log.call_args_list if call[0][0] == 10]  # logging.DEBUG = 10
        assert len(debug_calls) > 0
        assert "Query executed" in str(debug_calls[0])

    def test_no_stats_collection_when_disabled(self, mock_engine: Engine) -> None:
        """Test that statistics are not collected when collect_stats=False."""
        middleware = QueryTimingMiddleware(
            engine=mock_engine, collect_stats=False
        )
        middleware.install()

        # Execute a query
        with mock_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Verify stats is None
        assert middleware.stats is None
        assert middleware.get_stats() is None

    @patch("infrastructure.db.middleware.query_timing.time.perf_counter")
    def test_multiple_connections(
        self, mock_time: Mock, mock_engine: Engine
    ) -> None:
        """Test middleware works with multiple concurrent connections."""
        mock_time.side_effect = [
            0.0,
            0.050,  # Connection 1, Query 1: 50ms
            0.050,
            0.100,  # Connection 2, Query 1: 50ms
            0.100,
            0.150,  # Connection 1, Query 2: 50ms
        ]

        middleware = QueryTimingMiddleware(engine=mock_engine)
        middleware.install()

        # Execute queries on different connections
        with mock_engine.connect() as conn1:
            conn1.execute(text("SELECT 1"))
            with mock_engine.connect() as conn2:
                conn2.execute(text("SELECT 2"))
            conn1.execute(text("SELECT 3"))

        # Verify all queries counted
        stats = middleware.get_stats()
        assert stats.total_queries == 3


class TestInstallQueryTiming:
    """Tests for install_query_timing convenience function."""

    def test_install_returns_middleware(self, mock_engine: Engine) -> None:
        """Test that install_query_timing returns middleware instance."""
        middleware = install_query_timing(mock_engine)

        assert isinstance(middleware, QueryTimingMiddleware)
        assert middleware.engine == mock_engine

    def test_install_registers_events(self, mock_engine: Engine) -> None:
        """Test that install_query_timing registers events."""
        middleware = install_query_timing(mock_engine)

        before_events = event.contains(
            mock_engine, "before_cursor_execute", middleware._before_cursor_execute
        )
        after_events = event.contains(
            mock_engine, "after_cursor_execute", middleware._after_cursor_execute
        )

        assert before_events is True
        assert after_events is True

    def test_install_with_custom_config(self, mock_engine: Engine) -> None:
        """Test install_query_timing with custom configuration."""
        middleware = install_query_timing(
            mock_engine,
            slow_query_threshold_ms=200.0,
            log_all_queries=True,
            collect_stats=False,
        )

        assert middleware.slow_query_threshold_ms == 200.0
        assert middleware.log_all_queries is True
        assert middleware.collect_stats is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @patch("infrastructure.db.middleware.query_timing.time.perf_counter")
    def test_missing_start_time(
        self, mock_time: Mock, mock_engine: Engine
    ) -> None:
        """Test handling of missing start time in context."""
        middleware = QueryTimingMiddleware(engine=mock_engine)

        # Create mock context without _query_start_time
        mock_context = MagicMock()
        mock_context._query_start_time = None

        # Call after_execute without before_execute
        # Should not raise exception
        middleware._after_cursor_execute(
            conn=MagicMock(),
            cursor=MagicMock(),
            statement="SELECT 1",
            parameters=None,
            context=mock_context,
            executemany=False,
        )

    def test_empty_statement(self, mock_engine: Engine) -> None:
        """Test handling of empty SQL statement."""
        query_type = QueryStats._get_query_type("")
        assert query_type == "OTHER"

    def test_whitespace_only_statement(self, mock_engine: Engine) -> None:
        """Test handling of whitespace-only SQL statement."""
        query_type = QueryStats._get_query_type("   \n\t  ")
        assert query_type == "OTHER"

    def test_case_insensitive_query_type(self) -> None:
        """Test that query type detection is case-insensitive."""
        assert QueryStats._get_query_type("select * from users") == "SELECT"
        assert QueryStats._get_query_type("SELECT * FROM USERS") == "SELECT"
        assert QueryStats._get_query_type("SeLeCt * FrOm UsErS") == "SELECT"

    def test_zero_duration(self, query_stats: QueryStats) -> None:
        """Test handling of zero-duration queries."""
        query_stats.add_query("SELECT 1", 0.0, slow_threshold_ms=100.0)

        assert query_stats.total_queries == 1
        assert query_stats.slow_queries == 0
        assert query_stats.get_average_duration() == 0.0

    def test_negative_threshold_edge_case(self, mock_engine: Engine) -> None:
        """Test initialization with negative threshold."""
        # Should not raise, but behavior might be unusual
        middleware = QueryTimingMiddleware(
            engine=mock_engine, slow_query_threshold_ms=-1.0
        )
        assert middleware.slow_query_threshold_ms == -1.0
