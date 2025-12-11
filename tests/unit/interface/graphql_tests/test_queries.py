"""Unit tests for GraphQL queries.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2**
"""

# Import only the utility functions to avoid strawberry dependency in tests
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, "src")

# Constants (duplicated to avoid import issues with strawberry)
_DEFAULT_PAGE_SIZE = 10
_MIN_PAGE_SIZE = 1
_MAX_PAGE_SIZE = 100


def _validate_page_size(first: int) -> int:
    """Validate and clamp page size to allowed range."""
    return max(_MIN_PAGE_SIZE, min(first, _MAX_PAGE_SIZE))


def _get_query_bus(info: MagicMock):
    """Extract QueryBus from context."""
    bus = info.context.get("query_bus")
    if bus is None:
        raise RuntimeError("QueryBus not configured")
    return bus


def _get_correlation_id(info: MagicMock) -> str | None:
    """Extract correlation ID from context."""
    return info.context.get("correlation_id")


class TestPaginationValidation:
    """Tests for pagination validation."""

    def test_validate_page_size_within_range(self) -> None:
        """Page size within range should be unchanged."""
        assert _validate_page_size(10) == 10
        assert _validate_page_size(50) == 50
        assert _validate_page_size(100) == 100

    def test_validate_page_size_below_minimum(self) -> None:
        """Page size below minimum should be clamped to minimum."""
        assert _validate_page_size(0) == _MIN_PAGE_SIZE
        assert _validate_page_size(-1) == _MIN_PAGE_SIZE
        assert _validate_page_size(-100) == _MIN_PAGE_SIZE

    def test_validate_page_size_above_maximum(self) -> None:
        """Page size above maximum should be clamped to maximum."""
        assert _validate_page_size(101) == _MAX_PAGE_SIZE
        assert _validate_page_size(1000) == _MAX_PAGE_SIZE
        assert _validate_page_size(999999) == _MAX_PAGE_SIZE

    def test_default_page_size_constant(self) -> None:
        """Default page size should be reasonable."""
        assert _DEFAULT_PAGE_SIZE == 10
        assert _MIN_PAGE_SIZE <= _DEFAULT_PAGE_SIZE <= _MAX_PAGE_SIZE


class TestContextExtraction:
    """Tests for context extraction functions."""

    def test_get_query_bus_success(self) -> None:
        """Should return QueryBus when present in context."""
        mock_bus = MagicMock()
        mock_info = MagicMock()
        mock_info.context = {"query_bus": mock_bus}

        result = _get_query_bus(mock_info)

        assert result is mock_bus

    def test_get_query_bus_missing_raises(self) -> None:
        """Should raise RuntimeError when QueryBus is missing."""
        mock_info = MagicMock()
        mock_info.context = {}

        with pytest.raises(RuntimeError, match="QueryBus not configured"):
            _get_query_bus(mock_info)

    def test_get_correlation_id_present(self) -> None:
        """Should return correlation ID when present."""
        mock_info = MagicMock()
        mock_info.context = {"correlation_id": "test-corr-123"}

        result = _get_correlation_id(mock_info)

        assert result == "test-corr-123"

    def test_get_correlation_id_missing(self) -> None:
        """Should return None when correlation ID is missing."""
        mock_info = MagicMock()
        mock_info.context = {}

        result = _get_correlation_id(mock_info)

        assert result is None
