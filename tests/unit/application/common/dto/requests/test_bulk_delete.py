"""Tests for bulk delete DTOs.

**Feature: realistic-test-coverage**
**Validates: Requirements for architecture-validation-fixes-2025**
"""

import pytest
from pydantic import ValidationError

from application.common.dto.requests.bulk_delete import (
    BulkDeleteRequest,
    BulkDeleteResponse,
)


class TestBulkDeleteRequest:
    """Tests for BulkDeleteRequest."""

    def test_valid_request(self) -> None:
        """Test creating valid request."""
        request = BulkDeleteRequest(ids=["id1", "id2", "id3"])
        assert request.ids == ["id1", "id2", "id3"]

    def test_single_id(self) -> None:
        """Test request with single ID."""
        request = BulkDeleteRequest(ids=["id1"])
        assert len(request.ids) == 1

    def test_empty_ids_fails(self) -> None:
        """Test empty IDs list fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            BulkDeleteRequest(ids=[])
        assert "min_length" in str(exc_info.value).lower() or "1" in str(exc_info.value)

    def test_ids_required(self) -> None:
        """Test IDs field is required."""
        with pytest.raises(ValidationError):
            BulkDeleteRequest()

    def test_serialization(self) -> None:
        """Test request serialization."""
        request = BulkDeleteRequest(ids=["id1", "id2"])
        data = request.model_dump()
        assert data["ids"] == ["id1", "id2"]


class TestBulkDeleteResponse:
    """Tests for BulkDeleteResponse."""

    def test_valid_response(self) -> None:
        """Test creating valid response."""
        response = BulkDeleteResponse(deleted_count=5, failed_ids=["id1"])
        assert response.deleted_count == 5
        assert response.failed_ids == ["id1"]

    def test_default_failed_ids(self) -> None:
        """Test default empty failed_ids."""
        response = BulkDeleteResponse(deleted_count=3)
        assert response.failed_ids == []

    def test_zero_deleted_count(self) -> None:
        """Test zero deleted count is valid."""
        response = BulkDeleteResponse(deleted_count=0)
        assert response.deleted_count == 0

    def test_negative_deleted_count_fails(self) -> None:
        """Test negative deleted count fails."""
        with pytest.raises(ValidationError):
            BulkDeleteResponse(deleted_count=-1)

    def test_all_failed(self) -> None:
        """Test response with all failures."""
        response = BulkDeleteResponse(
            deleted_count=0,
            failed_ids=["id1", "id2", "id3"],
        )
        assert response.deleted_count == 0
        assert len(response.failed_ids) == 3

    def test_serialization(self) -> None:
        """Test response serialization."""
        response = BulkDeleteResponse(deleted_count=2, failed_ids=["id3"])
        data = response.model_dump()
        assert data["deleted_count"] == 2
        assert data["failed_ids"] == ["id3"]
