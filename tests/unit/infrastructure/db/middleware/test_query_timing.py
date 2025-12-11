"""Tests for infrastructure/db/middleware/query_timing.py - Query timing middleware."""

from src.infrastructure.db.middleware.query_timing import QueryStats


class TestQueryStats:
    """Tests for QueryStats class."""

    def test_init_defaults(self):
        stats = QueryStats()
        assert stats.total_queries == 0
        assert stats.slow_queries == 0
        assert stats.total_duration_ms == 0.0
        assert stats.queries_by_type == {}
        assert stats.slowest_queries == []

    def test_add_query_increments_total(self):
        stats = QueryStats()
        stats.add_query("SELECT * FROM users", 50.0)
        assert stats.total_queries == 1

    def test_add_query_accumulates_duration(self):
        stats = QueryStats()
        stats.add_query("SELECT * FROM users", 50.0)
        stats.add_query("SELECT * FROM orders", 30.0)
        assert stats.total_duration_ms == 80.0

    def test_add_query_tracks_slow_queries(self):
        stats = QueryStats()
        stats.add_query("SELECT * FROM users", 150.0, slow_threshold_ms=100.0)
        assert stats.slow_queries == 1

    def test_add_query_fast_not_slow(self):
        stats = QueryStats()
        stats.add_query("SELECT * FROM users", 50.0, slow_threshold_ms=100.0)
        assert stats.slow_queries == 0

    def test_add_query_categorizes_select(self):
        stats = QueryStats()
        stats.add_query("SELECT * FROM users", 50.0)
        assert stats.queries_by_type.get("SELECT") == 1

    def test_add_query_categorizes_insert(self):
        stats = QueryStats()
        stats.add_query("INSERT INTO users VALUES (...)", 50.0)
        assert stats.queries_by_type.get("INSERT") == 1

    def test_add_query_categorizes_update(self):
        stats = QueryStats()
        stats.add_query("UPDATE users SET name = 'test'", 50.0)
        assert stats.queries_by_type.get("UPDATE") == 1

    def test_add_query_categorizes_delete(self):
        stats = QueryStats()
        stats.add_query("DELETE FROM users WHERE id = 1", 50.0)
        assert stats.queries_by_type.get("DELETE") == 1

    def test_add_query_categorizes_begin(self):
        stats = QueryStats()
        stats.add_query("BEGIN", 5.0)
        assert stats.queries_by_type.get("BEGIN") == 1

    def test_add_query_categorizes_commit(self):
        stats = QueryStats()
        stats.add_query("COMMIT", 5.0)
        assert stats.queries_by_type.get("COMMIT") == 1

    def test_add_query_categorizes_rollback(self):
        stats = QueryStats()
        stats.add_query("ROLLBACK", 5.0)
        assert stats.queries_by_type.get("ROLLBACK") == 1

    def test_add_query_categorizes_other(self):
        stats = QueryStats()
        stats.add_query("CREATE TABLE test (...)", 50.0)
        assert stats.queries_by_type.get("OTHER") == 1

    def test_add_query_tracks_slowest(self):
        stats = QueryStats()
        stats.add_query("SELECT slow", 200.0, slow_threshold_ms=100.0)
        assert len(stats.slowest_queries) == 1
        assert stats.slowest_queries[0][0] == "SELECT slow"
        assert stats.slowest_queries[0][1] == 200.0

    def test_slowest_queries_limited_to_10(self):
        stats = QueryStats()
        for i in range(15):
            stats.add_query(f"SELECT {i}", 100.0 + i, slow_threshold_ms=100.0)
        assert len(stats.slowest_queries) == 10

    def test_slowest_queries_sorted_descending(self):
        stats = QueryStats()
        stats.add_query("SELECT fast", 110.0, slow_threshold_ms=100.0)
        stats.add_query("SELECT slow", 200.0, slow_threshold_ms=100.0)
        stats.add_query("SELECT medium", 150.0, slow_threshold_ms=100.0)
        assert stats.slowest_queries[0][1] == 200.0
        assert stats.slowest_queries[1][1] == 150.0
        assert stats.slowest_queries[2][1] == 110.0


class TestQueryStatsGetQueryType:
    """Tests for _get_query_type static method."""

    def test_select_uppercase(self):
        assert QueryStats._get_query_type("SELECT * FROM users") == "SELECT"

    def test_select_lowercase(self):
        assert QueryStats._get_query_type("select * from users") == "SELECT"

    def test_select_with_whitespace(self):
        assert QueryStats._get_query_type("  SELECT * FROM users") == "SELECT"

    def test_insert(self):
        assert QueryStats._get_query_type("INSERT INTO users") == "INSERT"

    def test_update(self):
        assert QueryStats._get_query_type("UPDATE users SET") == "UPDATE"

    def test_delete(self):
        assert QueryStats._get_query_type("DELETE FROM users") == "DELETE"

    def test_begin(self):
        assert QueryStats._get_query_type("BEGIN") == "BEGIN"

    def test_commit(self):
        assert QueryStats._get_query_type("COMMIT") == "COMMIT"

    def test_rollback(self):
        assert QueryStats._get_query_type("ROLLBACK") == "ROLLBACK"

    def test_other(self):
        assert QueryStats._get_query_type("CREATE TABLE") == "OTHER"
        assert QueryStats._get_query_type("DROP TABLE") == "OTHER"
        assert QueryStats._get_query_type("ALTER TABLE") == "OTHER"


class TestQueryStatsGetAverageDuration:
    """Tests for get_average_duration method."""

    def test_zero_queries(self):
        stats = QueryStats()
        assert stats.get_average_duration() == 0.0

    def test_single_query(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 100.0)
        assert stats.get_average_duration() == 100.0

    def test_multiple_queries(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 100.0)
        stats.add_query("SELECT 2", 200.0)
        stats.add_query("SELECT 3", 300.0)
        assert stats.get_average_duration() == 200.0


class TestQueryStatsGetSummary:
    """Tests for get_summary method."""

    def test_summary_returns_dict(self):
        stats = QueryStats()
        summary = stats.get_summary()
        assert isinstance(summary, dict)

    def test_summary_contains_total_queries(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 50.0)
        summary = stats.get_summary()
        assert summary["total_queries"] == 1

    def test_summary_contains_slow_queries(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 150.0, slow_threshold_ms=100.0)
        summary = stats.get_summary()
        assert summary["slow_queries"] == 1

    def test_summary_contains_slow_query_percentage(self):
        stats = QueryStats()
        stats.add_query("SELECT fast", 50.0, slow_threshold_ms=100.0)
        stats.add_query("SELECT slow", 150.0, slow_threshold_ms=100.0)
        summary = stats.get_summary()
        assert summary["slow_query_percentage"] == 50.0

    def test_summary_contains_total_duration(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 100.5)
        summary = stats.get_summary()
        assert summary["total_duration_ms"] == 100.5

    def test_summary_contains_average_duration(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 100.0)
        stats.add_query("SELECT 2", 200.0)
        summary = stats.get_summary()
        assert summary["average_duration_ms"] == 150.0

    def test_summary_contains_queries_by_type(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 50.0)
        stats.add_query("INSERT INTO t", 50.0)
        summary = stats.get_summary()
        assert "SELECT" in summary["queries_by_type"]
        assert "INSERT" in summary["queries_by_type"]

    def test_summary_truncates_long_statements(self):
        stats = QueryStats()
        long_query = "SELECT " + "x" * 300
        stats.add_query(long_query, 150.0, slow_threshold_ms=100.0)
        summary = stats.get_summary()
        assert len(summary["slowest_queries"][0]["statement"]) <= 203  # 200 + "..."

    def test_summary_rounds_durations(self):
        stats = QueryStats()
        stats.add_query("SELECT 1", 100.123456)
        summary = stats.get_summary()
        assert summary["total_duration_ms"] == 100.12
        assert summary["average_duration_ms"] == 100.12
