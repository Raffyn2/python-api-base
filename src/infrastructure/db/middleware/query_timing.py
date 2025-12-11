"""Query timing middleware for SQLAlchemy.

Monitors SQL query execution time and logs slow queries.

**Feature: performance-monitoring-2025**
**Validates: Action Items - Performance Profiling**
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import event
from sqlalchemy.pool import Pool

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection, Engine

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class QueryStats:
    """Statistics for query execution."""

    total_queries: int = 0
    slow_queries: int = 0
    total_duration_ms: float = 0.0
    queries_by_type: dict[str, int] = field(default_factory=dict)
    slowest_queries: list[tuple[str, float]] = field(default_factory=list)

    def add_query(self, statement: str, duration_ms: float, slow_threshold_ms: float = 100.0) -> None:
        """Add a query execution to statistics.

        Args:
            statement: SQL statement
            duration_ms: Query duration in milliseconds
            slow_threshold_ms: Threshold to consider a query slow
        """
        self.total_queries += 1
        self.total_duration_ms += duration_ms

        # Categorize by query type
        query_type = self._get_query_type(statement)
        self.queries_by_type[query_type] = self.queries_by_type.get(query_type, 0) + 1

        # Track slow queries
        if duration_ms >= slow_threshold_ms:
            self.slow_queries += 1
            self.slowest_queries.append((statement, duration_ms))
            # Keep only top 10 slowest
            self.slowest_queries = sorted(
                self.slowest_queries,
                key=lambda x: x[1],
                reverse=True,
            )[:10]

    @staticmethod
    def _get_query_type(statement: str) -> str:
        """Extract query type from SQL statement.

        Args:
            statement: SQL statement

        Returns:
            Query type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        query_types = ("SELECT", "INSERT", "UPDATE", "DELETE", "BEGIN", "COMMIT", "ROLLBACK")
        normalized = statement.strip().upper()
        return next(
            (qtype for qtype in query_types if normalized.startswith(qtype)),
            "OTHER",
        )

    def get_average_duration(self) -> float:
        """Calculate average query duration.

        Returns:
            Average duration in milliseconds
        """
        if self.total_queries == 0:
            return 0.0
        return self.total_duration_ms / self.total_queries

    def get_summary(self) -> dict[str, Any]:
        """Get statistics summary.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_queries": self.total_queries,
            "slow_queries": self.slow_queries,
            "slow_query_percentage": (
                (self.slow_queries / self.total_queries * 100) if self.total_queries > 0 else 0.0
            ),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "average_duration_ms": round(self.get_average_duration(), 2),
            "queries_by_type": self.queries_by_type,
            "slowest_queries": [
                {
                    "statement": stmt[:200] + "..." if len(stmt) > 200 else stmt,
                    "duration_ms": round(duration, 2),
                }
                for stmt, duration in self.slowest_queries
            ],
        }


class QueryTimingMiddleware:
    """SQLAlchemy middleware for query timing and logging.

    Features:
    - Logs slow queries (> threshold)
    - Collects query statistics
    - Monitors query patterns
    - Tracks database performance

    Example:
        >>> engine = create_engine(...)
        >>> middleware = QueryTimingMiddleware(
        ...     engine=engine,
        ...     slow_query_threshold_ms=100.0,
        ...     log_all_queries=False,
        ... )
        >>> middleware.install()
        >>> # ... use engine normally ...
        >>> stats = middleware.get_stats()
        >>> print(stats.get_summary())
    """

    def __init__(
        self,
        engine: Engine,
        slow_query_threshold_ms: float = 100.0,
        log_all_queries: bool = False,
        collect_stats: bool = True,
    ):
        """Initialize query timing middleware.

        Args:
            engine: SQLAlchemy engine
            slow_query_threshold_ms: Threshold to consider a query slow (milliseconds)
            log_all_queries: If True, log all queries (not just slow ones)
            collect_stats: If True, collect query statistics
        """
        self.engine = engine
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.log_all_queries = log_all_queries
        self.collect_stats = collect_stats
        self.stats = QueryStats() if collect_stats else None
        self._installed = False

    def install(self) -> None:
        """Install timing hooks on the engine."""
        if self._installed:
            logger.warning("Query timing middleware already installed")
            return

        event.listen(self.engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(self.engine, "after_cursor_execute", self._after_cursor_execute)
        event.listen(Pool, "connect", self._on_connect)
        event.listen(Pool, "checkout", self._on_checkout)

        self._installed = True
        logger.info(
            "Query timing middleware installed",
            slow_query_threshold_ms=self.slow_query_threshold_ms,
            log_all_queries=self.log_all_queries,
            collect_stats=self.collect_stats,
        )

    def uninstall(self) -> None:
        """Remove timing hooks from the engine."""
        if not self._installed:
            return

        event.remove(self.engine, "before_cursor_execute", self._before_cursor_execute)
        event.remove(self.engine, "after_cursor_execute", self._after_cursor_execute)
        event.remove(Pool, "connect", self._on_connect)
        event.remove(Pool, "checkout", self._on_checkout)

        self._installed = False
        logger.info("Query timing middleware uninstalled")

    def _before_cursor_execute(
        self,
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Event handler before query execution.

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: If True, multiple parameters are being executed
        """
        # Store start time in context
        context._query_start_time = time.perf_counter()
        context._query_statement = statement
        context._query_executemany = executemany

    def _after_cursor_execute(
        self,
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Event handler after query execution.

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: If True, multiple parameters were executed
        """
        # Calculate duration
        start_time = getattr(context, "_query_start_time", None)
        if start_time is None:
            return

        duration_s = time.perf_counter() - start_time
        duration_ms = duration_s * 1000

        # Collect statistics
        if self.collect_stats and self.stats:
            self.stats.add_query(statement, duration_ms, self.slow_query_threshold_ms)

        # Log slow queries
        is_slow = duration_ms >= self.slow_query_threshold_ms
        if is_slow or self.log_all_queries:
            query_type = QueryStats._get_query_type(statement)

            if is_slow:
                logger.warning(
                    "Slow query detected",
                    duration_ms=round(duration_ms, 2),
                    statement=statement[:500],
                    executemany=executemany,
                    is_slow=is_slow,
                    query_type=query_type,
                    operation="DB_SLOW_QUERY",
                    threshold_ms=self.slow_query_threshold_ms,
                )
            else:
                logger.debug(
                    "Query executed",
                    duration_ms=round(duration_ms, 2),
                    statement=statement[:500],
                    executemany=executemany,
                    is_slow=is_slow,
                    query_type=query_type,
                    operation="DB_QUERY",
                )

    def _on_connect(self, dbapi_conn: Any, connection_record: Any) -> None:
        """Event handler when new connection is created.

        Args:
            dbapi_conn: DB-API connection
            connection_record: Connection record
        """
        logger.debug("New database connection created")

    def _on_checkout(self, dbapi_conn: Any, connection_record: Any, connection_proxy: Any) -> None:
        """Event handler when connection is checked out from pool.

        Args:
            dbapi_conn: DB-API connection
            connection_record: Connection record
            connection_proxy: Connection proxy
        """
        logger.debug("Connection checked out from pool")

    def get_stats(self) -> QueryStats | None:
        """Get collected query statistics.

        Returns:
            QueryStats object or None if stats collection is disabled
        """
        return self.stats

    def reset_stats(self) -> None:
        """Reset collected statistics."""
        if self.stats:
            self.stats = QueryStats()
            logger.info("Query statistics reset")


def install_query_timing(
    engine: Engine,
    slow_query_threshold_ms: float = 100.0,
    log_all_queries: bool = False,
    collect_stats: bool = True,
) -> QueryTimingMiddleware:
    """Install query timing middleware on engine.

    This is a convenience function that creates and installs the middleware.

    Args:
        engine: SQLAlchemy engine
        slow_query_threshold_ms: Threshold to consider a query slow (milliseconds)
        log_all_queries: If True, log all queries (not just slow ones)
        collect_stats: If True, collect query statistics

    Returns:
        Installed QueryTimingMiddleware instance

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine("postgresql://...")
        >>> middleware = install_query_timing(
        ...     engine,
        ...     slow_query_threshold_ms=100.0,
        ...     log_all_queries=False,
        ... )
        >>> # Later, get statistics
        >>> stats = middleware.get_stats()
        >>> print(stats.get_summary())
    """
    middleware = QueryTimingMiddleware(
        engine=engine,
        slow_query_threshold_ms=slow_query_threshold_ms,
        log_all_queries=log_all_queries,
        collect_stats=collect_stats,
    )
    middleware.install()
    return middleware


__all__ = [
    "QueryStats",
    "QueryTimingMiddleware",
    "install_query_timing",
]
