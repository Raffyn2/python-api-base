"""Tests for paginated response DTO.

**Feature: realistic-test-coverage**
**Validates: Requirements for application-layer-improvements-2025**
"""

import pytest
from pydantic import ValidationError

from application.common.dto.responses.paginated_response import PaginatedResponse


class TestPaginatedResponse:
    """Tests for PaginatedResponse."""

    def test_create_response(self) -> None:
        """Test creating paginated response."""
        response = PaginatedResponse[dict](
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
        """Test pages calculation."""
        response = PaginatedResponse[str](
            items=["a", "b"],
            total=100,
            page=1,
            size=10,
        )
        assert response.pages == 10

    def test_pages_with_remainder(self) -> None:
        """Test pages calculation with remainder."""
        response = PaginatedResponse[str](
            items=["a"],
            total=25,
            page=1,
            size=10,
        )
        assert response.pages == 3  # 25 / 10 = 2.5 -> 3 pages

    def test_pages_zero_total(self) -> None:
        """Test pages is 0 when total is 0."""
        response = PaginatedResponse[str](
            items=[],
            total=0,
            page=1,
            size=10,
        )
        assert response.pages == 0

    def test_has_next_true(self) -> None:
        """Test has_next is True when not on last page."""
        response = PaginatedResponse[str](
            items=["a"],
            total=100,
            page=1,
            size=10,
        )
        assert response.has_next is True

    def test_has_next_false_on_last_page(self) -> None:
        """Test has_next is False on last page."""
        response = PaginatedResponse[str](
            items=["a"],
            total=100,
            page=10,
            size=10,
        )
        assert response.has_next is False

    def test_has_next_false_empty(self) -> None:
        """Test has_next is False when empty."""
        response = PaginatedResponse[str](
            items=[],
            total=0,
            page=1,
            size=10,
        )
        assert response.has_next is False

    def test_has_previous_false_on_first_page(self) -> None:
        """Test has_previous is False on first page."""
        response = PaginatedResponse[str](
            items=["a"],
            total=100,
            page=1,
            size=10,
        )
        assert response.has_previous is False

    def test_has_previous_true(self) -> None:
        """Test has_previous is True when not on first page."""
        response = PaginatedResponse[str](
            items=["a"],
            total=100,
            page=2,
            size=10,
        )
        assert response.has_previous is True

    def test_page_minimum(self) -> None:
        """Test page minimum validation."""
        with pytest.raises(ValidationError):
            PaginatedResponse[str](
                items=[],
                total=0,
                page=0,
                size=10,
            )

    def test_size_minimum(self) -> None:
        """Test size minimum validation."""
        with pytest.raises(ValidationError):
            PaginatedResponse[str](
                items=[],
                total=0,
                page=1,
                size=0,
            )

    def test_size_maximum(self) -> None:
        """Test size maximum validation."""
        with pytest.raises(ValidationError):
            PaginatedResponse[str](
                items=[],
                total=0,
                page=1,
                size=101,
            )

    def test_total_minimum(self) -> None:
        """Test total minimum validation."""
        with pytest.raises(ValidationError):
            PaginatedResponse[str](
                items=[],
                total=-1,
                page=1,
                size=10,
            )

    def test_serialization(self) -> None:
        """Test response serialization includes computed fields."""
        response = PaginatedResponse[dict](
            items=[{"id": "1"}],
            total=50,
            page=2,
            size=10,
        )
        data = response.model_dump()

        assert data["items"] == [{"id": "1"}]
        assert data["total"] == 50
        assert data["page"] == 2
        assert data["size"] == 10
        assert data["pages"] == 5
        assert data["has_next"] is True
        assert data["has_previous"] is True

    def test_with_typed_items(self) -> None:
        """Test response with typed items."""
        response = PaginatedResponse[int](
            items=[1, 2, 3],
            total=10,
            page=1,
            size=3,
        )
        assert response.items == [1, 2, 3]

    def test_from_attributes_config(self) -> None:
        """Test from_attributes config is set."""
        assert PaginatedResponse.model_config.get("from_attributes") is True
