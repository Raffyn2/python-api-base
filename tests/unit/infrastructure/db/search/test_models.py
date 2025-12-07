"""Tests for search models module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.8, 7.9, 7.10**
"""

import pytest

from infrastructure.db.search.models import SearchQuery, SearchResult


class TestSearchQuery:
    """Tests for SearchQuery."""

    def test_create_minimal(self) -> None:
        """Test creating minimal search query."""
        query = SearchQuery(query="test")
        assert query.query == "test"

    def test_default_values(self) -> None:
        """Test default values."""
        query = SearchQuery(query="test")
        assert query.filters == {}
        assert query.sort == []
        assert query.page == 1
        assert query.page_size == 20
        assert query.highlight_fields == []

    def test_with_filters(self) -> None:
        """Test query with filters."""
        query = SearchQuery(
            query="test",
            filters={"status": "active", "category": "books"},
        )
        assert query.filters["status"] == "active"
        assert query.filters["category"] == "books"

    def test_with_sort(self) -> None:
        """Test query with sort."""
        query = SearchQuery(
            query="test",
            sort=[("created_at", "desc"), ("name", "asc")],
        )
        assert len(query.sort) == 2
        assert query.sort[0] == ("created_at", "desc")

    def test_with_pagination(self) -> None:
        """Test query with pagination."""
        query = SearchQuery(
            query="test",
            page=3,
            page_size=50,
        )
        assert query.page == 3
        assert query.page_size == 50

    def test_with_highlight_fields(self) -> None:
        """Test query with highlight fields."""
        query = SearchQuery(
            query="test",
            highlight_fields=["title", "description"],
        )
        assert "title" in query.highlight_fields
        assert "description" in query.highlight_fields

    def test_is_frozen(self) -> None:
        """Test query is immutable."""
        query = SearchQuery(query="test")
        with pytest.raises(AttributeError):
            query.query = "new"


class TestSearchResult:
    """Tests for SearchResult."""

    def test_create_result(self) -> None:
        """Test creating search result."""
        result = SearchResult[dict](
            items=({"id": "1"}, {"id": "2"}),
            total=100,
            page=1,
            page_size=10,
        )
        assert len(result.items) == 2
        assert result.total == 100

    def test_has_more_true(self) -> None:
        """Test has_more is True when more pages exist."""
        result = SearchResult[str](
            items=("a", "b"),
            total=100,
            page=1,
            page_size=10,
        )
        assert result.has_more is True

    def test_has_more_false_on_last_page(self) -> None:
        """Test has_more is False on last page."""
        result = SearchResult[str](
            items=("a", "b"),
            total=100,
            page=10,
            page_size=10,
        )
        assert result.has_more is False

    def test_has_more_false_when_empty(self) -> None:
        """Test has_more is False when empty."""
        result = SearchResult[str](
            items=(),
            total=0,
            page=1,
            page_size=10,
        )
        assert result.has_more is False

    def test_with_facets(self) -> None:
        """Test result with facets."""
        result = SearchResult[dict](
            items=(),
            total=0,
            page=1,
            page_size=10,
            facets={
                "category": {"books": 10, "electronics": 5},
                "status": {"active": 12, "inactive": 3},
            },
        )
        assert result.facets["category"]["books"] == 10

    def test_with_highlights(self) -> None:
        """Test result with highlights."""
        result = SearchResult[dict](
            items=(),
            total=0,
            page=1,
            page_size=10,
            highlights={
                "doc1": ["<em>test</em> result"],
            },
        )
        assert "doc1" in result.highlights

    def test_default_facets_empty(self) -> None:
        """Test default facets is empty."""
        result = SearchResult[str](
            items=(),
            total=0,
            page=1,
            page_size=10,
        )
        assert result.facets == {}

    def test_default_highlights_empty(self) -> None:
        """Test default highlights is empty."""
        result = SearchResult[str](
            items=(),
            total=0,
            page=1,
            page_size=10,
        )
        assert result.highlights == {}

    def test_is_frozen(self) -> None:
        """Test result is immutable."""
        result = SearchResult[str](
            items=(),
            total=0,
            page=1,
            page_size=10,
        )
        with pytest.raises(AttributeError):
            result.total = 100
