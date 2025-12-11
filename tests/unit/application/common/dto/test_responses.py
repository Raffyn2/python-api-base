"""Unit tests for response DTOs.

Tests ApiResponse and PaginatedResponse DTOs.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from application.common.dto import ApiResponse, PaginatedResponse


class TestApiResponse:
    """Tests for ApiResponse DTO."""

    def test_basic_creation(self) -> None:
        """Test basic ApiResponse creation."""
        response = ApiResponse(data={"id": "123"})
        assert response.data == {"id": "123"}
        assert response.message == "Success"
        assert response.status_code == 200

    def test_with_custom_message(self) -> None:
        """Test ApiResponse with custom message."""
        response = ApiResponse(
            data="test",
            message="Custom message",
        )
        assert response.message == "Custom message"

    def test_with_status_code(self) -> None:
        """Test ApiResponse with custom status code."""
        response = ApiResponse(
            data=None,
            status_code=201,
        )
        assert response.status_code == 201

    def test_with_request_id(self) -> None:
        """Test ApiResponse with request ID."""
        response = ApiResponse(
            data={},
            request_id="req-123",
        )
        assert response.request_id == "req-123"

    def test_timestamp_is_set(self) -> None:
        """Test timestamp is automatically set."""
        response = ApiResponse(data="test")
        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)

    def test_invalid_status_code_too_low(self) -> None:
        """Test invalid status code below 100."""
        with pytest.raises(ValidationError):
            ApiResponse(data="test", status_code=99)

    def test_invalid_status_code_too_high(self) -> None:
        """Test invalid status code above 599."""
        with pytest.raises(ValidationError):
            ApiResponse(data="test", status_code=600)

    def test_generic_type_dict(self) -> None:
        """Test ApiResponse with dict data."""
        response = ApiResponse[dict](data={"key": "value"})
        assert response.data["key"] == "value"

    def test_generic_type_list(self) -> None:
        """Test ApiResponse with list data."""
        response = ApiResponse[list](data=[1, 2, 3])
        assert len(response.data) == 3


class TestPaginatedResponse:
    """Tests for PaginatedResponse DTO."""

    def test_basic_creation(self) -> None:
        """Test basic PaginatedResponse creation."""
        response = PaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            total=100,
            page=1,
            size=10,
        )
        assert len(response.items) == 2
        assert response.total == 100
        assert response.page == 1
        assert response.size == 10

    def test_pages_calculation(self) -> None:
        """Test total pages calculation."""
        response = PaginatedResponse(
            items=[],
            total=100,
            page=1,
            size=10,
        )
        assert response.pages == 10

    def test_pages_calculation_with_remainder(self) -> None:
        """Test pages calculation with remainder."""
        response = PaginatedResponse(
            items=[],
            total=25,
            page=1,
            size=10,
        )
        assert response.pages == 3

    def test_pages_zero_total(self) -> None:
        """Test pages is 0 when total is 0."""
        response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=10,
        )
        assert response.pages == 0

    def test_has_next_true(self) -> None:
        """Test has_next is True when not on last page."""
        response = PaginatedResponse(
            items=[],
            total=100,
            page=1,
            size=10,
        )
        assert response.has_next is True

    def test_has_next_false(self) -> None:
        """Test has_next is False on last page."""
        response = PaginatedResponse(
            items=[],
            total=100,
            page=10,
            size=10,
        )
        assert response.has_next is False

    def test_has_previous_true(self) -> None:
        """Test has_previous is True when not on first page."""
        response = PaginatedResponse(
            items=[],
            total=100,
            page=2,
            size=10,
        )
        assert response.has_previous is True

    def test_has_previous_false(self) -> None:
        """Test has_previous is False on first page."""
        response = PaginatedResponse(
            items=[],
            total=100,
            page=1,
            size=10,
        )
        assert response.has_previous is False

    def test_invalid_page_zero(self) -> None:
        """Test page cannot be 0."""
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                total=10,
                page=0,
                size=10,
            )

    def test_invalid_size_zero(self) -> None:
        """Test size cannot be 0."""
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                total=10,
                page=1,
                size=0,
            )

    def test_invalid_size_too_large(self) -> None:
        """Test size cannot exceed 100."""
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                total=10,
                page=1,
                size=101,
            )

    def test_invalid_negative_total(self) -> None:
        """Test total cannot be negative."""
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                total=-1,
                page=1,
                size=10,
            )

    def test_generic_type(self) -> None:
        """Test PaginatedResponse with typed items."""
        response = PaginatedResponse[dict](
            items=[{"id": "1"}],
            total=1,
            page=1,
            size=10,
        )
        assert response.items[0]["id"] == "1"
