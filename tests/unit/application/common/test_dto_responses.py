"""Unit tests for application/common/dto/responses.

Tests API response and paginated response DTOs.

**Feature: test-coverage-90-percent**
**Validates: Requirements 1.1**
"""

from datetime import UTC, datetime

import pytest

from application.common.dto.responses import (
    ApiResponse,
    PaginatedResponse,
)


class TestApiResponse:
    """Tests for ApiResponse DTO."""

    def test_create_api_response(self) -> None:
        """ApiResponse should wrap data with metadata."""
        response = ApiResponse(
            data={"id": "123", "name": "Test"},
            message="Success",
            status_code=200
        )
        
        assert response.data == {"id": "123", "name": "Test"}
        assert response.message == "Success"
        assert response.status_code == 200

    def test_api_response_default_values(self) -> None:
        """ApiResponse should have sensible defaults."""
        response = ApiResponse(data="test")
        
        assert response.message == "Success"
        assert response.status_code == 200
        assert response.request_id is None

    def test_api_response_timestamp(self) -> None:
        """ApiResponse should have UTC timestamp."""
        response = ApiResponse(data="test")
        
        assert isinstance(response.timestamp, datetime)
        assert response.timestamp.tzinfo == UTC

    def test_api_response_with_request_id(self) -> None:
        """ApiResponse should accept request_id."""
        response = ApiResponse(
            data="test",
            request_id="req-123-456"
        )
        
        assert response.request_id == "req-123-456"

    def test_api_response_generic_type(self) -> None:
        """ApiResponse should work with different data types."""
        # Dict
        dict_response = ApiResponse(data={"key": "value"})
        assert dict_response.data == {"key": "value"}
        
        # List
        list_response = ApiResponse(data=[1, 2, 3])
        assert list_response.data == [1, 2, 3]
        
        # String
        str_response = ApiResponse(data="hello")
        assert str_response.data == "hello"
        
        # None
        none_response = ApiResponse(data=None)
        assert none_response.data is None

    def test_api_response_status_code_validation(self) -> None:
        """ApiResponse should validate status code range."""
        # Valid codes
        ApiResponse(data="test", status_code=100)
        ApiResponse(data="test", status_code=599)
        
        # Invalid codes
        with pytest.raises(ValueError):
            ApiResponse(data="test", status_code=99)
        
        with pytest.raises(ValueError):
            ApiResponse(data="test", status_code=600)

    def test_api_response_serialization(self) -> None:
        """ApiResponse should serialize to dict."""
        response = ApiResponse(
            data={"id": "123"},
            message="Created",
            status_code=201
        )
        
        data = response.model_dump()
        
        assert data["data"] == {"id": "123"}
        assert data["message"] == "Created"
        assert data["status_code"] == 201


class TestPaginatedResponse:
    """Tests for PaginatedResponse DTO."""

    def test_create_paginated_response(self) -> None:
        """PaginatedResponse should store pagination data."""
        response = PaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            total=100,
            page=1,
            size=10
        )
        
        assert len(response.items) == 2
        assert response.total == 100
        assert response.page == 1
        assert response.size == 10

    def test_pages_calculation(self) -> None:
        """pages should calculate total pages correctly."""
        # Exact division
        response = PaginatedResponse(items=[], total=100, page=1, size=10)
        assert response.pages == 10
        
        # With remainder
        response = PaginatedResponse(items=[], total=101, page=1, size=10)
        assert response.pages == 11
        
        # Single page
        response = PaginatedResponse(items=[], total=5, page=1, size=10)
        assert response.pages == 1

    def test_pages_zero_total(self) -> None:
        """pages should return 0 for empty collection."""
        response = PaginatedResponse(items=[], total=0, page=1, size=10)
        
        assert response.pages == 0

    def test_has_next_true(self) -> None:
        """has_next should be True when not on last page."""
        response = PaginatedResponse(items=[], total=100, page=1, size=10)
        
        assert response.has_next is True

    def test_has_next_false(self) -> None:
        """has_next should be False on last page."""
        response = PaginatedResponse(items=[], total=100, page=10, size=10)
        
        assert response.has_next is False

    def test_has_previous_true(self) -> None:
        """has_previous should be True when not on first page."""
        response = PaginatedResponse(items=[], total=100, page=2, size=10)
        
        assert response.has_previous is True

    def test_has_previous_false(self) -> None:
        """has_previous should be False on first page."""
        response = PaginatedResponse(items=[], total=100, page=1, size=10)
        
        assert response.has_previous is False

    def test_page_validation(self) -> None:
        """page should be at least 1."""
        with pytest.raises(ValueError):
            PaginatedResponse(items=[], total=100, page=0, size=10)

    def test_size_validation(self) -> None:
        """size should be between 1 and 100."""
        # Valid
        PaginatedResponse(items=[], total=100, page=1, size=1)
        PaginatedResponse(items=[], total=100, page=1, size=100)
        
        # Invalid
        with pytest.raises(ValueError):
            PaginatedResponse(items=[], total=100, page=1, size=0)
        
        with pytest.raises(ValueError):
            PaginatedResponse(items=[], total=100, page=1, size=101)

    def test_total_validation(self) -> None:
        """total should be non-negative."""
        # Valid
        PaginatedResponse(items=[], total=0, page=1, size=10)
        
        # Invalid
        with pytest.raises(ValueError):
            PaginatedResponse(items=[], total=-1, page=1, size=10)

    def test_paginated_response_generic_type(self) -> None:
        """PaginatedResponse should work with different item types."""
        # Dict items
        dict_response = PaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            total=2, page=1, size=10
        )
        assert len(dict_response.items) == 2
        
        # String items
        str_response = PaginatedResponse(
            items=["a", "b", "c"],
            total=3, page=1, size=10
        )
        assert str_response.items == ["a", "b", "c"]

    def test_paginated_response_serialization(self) -> None:
        """PaginatedResponse should serialize with computed fields."""
        response = PaginatedResponse(
            items=[{"id": "1"}],
            total=50,
            page=2,
            size=10
        )
        
        data = response.model_dump()
        
        assert data["items"] == [{"id": "1"}]
        assert data["total"] == 50
        assert data["page"] == 2
        assert data["size"] == 10
        assert data["pages"] == 5
        assert data["has_next"] is True
        assert data["has_previous"] is True

    def test_edge_case_single_item(self) -> None:
        """PaginatedResponse should handle single item."""
        response = PaginatedResponse(
            items=[{"id": "1"}],
            total=1,
            page=1,
            size=10
        )
        
        assert response.pages == 1
        assert response.has_next is False
        assert response.has_previous is False
