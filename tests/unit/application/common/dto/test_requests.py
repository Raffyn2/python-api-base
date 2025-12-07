"""Unit tests for request DTOs.

Tests BulkDeleteRequest and BulkDeleteResponse DTOs.
"""

import pytest
from pydantic import ValidationError

from application.common.dto import BulkDeleteRequest, BulkDeleteResponse


class TestBulkDeleteRequest:
    """Tests for BulkDeleteRequest DTO."""

    def test_basic_creation(self) -> None:
        """Test basic BulkDeleteRequest creation."""
        request = BulkDeleteRequest(ids=["id1", "id2", "id3"])
        assert len(request.ids) == 3
        assert "id1" in request.ids

    def test_single_id(self) -> None:
        """Test BulkDeleteRequest with single ID."""
        request = BulkDeleteRequest(ids=["single-id"])
        assert len(request.ids) == 1

    def test_empty_list_raises(self) -> None:
        """Test empty list raises ValidationError."""
        with pytest.raises(ValidationError):
            BulkDeleteRequest(ids=[])

    def test_missing_ids_raises(self) -> None:
        """Test missing ids field raises ValidationError."""
        with pytest.raises(ValidationError):
            BulkDeleteRequest()


class TestBulkDeleteResponse:
    """Tests for BulkDeleteResponse DTO."""

    def test_basic_creation(self) -> None:
        """Test basic BulkDeleteResponse creation."""
        response = BulkDeleteResponse(deleted_count=5)
        assert response.deleted_count == 5
        assert response.failed_ids == []

    def test_with_failed_ids(self) -> None:
        """Test BulkDeleteResponse with failed IDs."""
        response = BulkDeleteResponse(
            deleted_count=3,
            failed_ids=["id4", "id5"],
        )
        assert response.deleted_count == 3
        assert len(response.failed_ids) == 2

    def test_zero_deleted(self) -> None:
        """Test BulkDeleteResponse with zero deleted."""
        response = BulkDeleteResponse(deleted_count=0)
        assert response.deleted_count == 0

    def test_negative_count_raises(self) -> None:
        """Test negative deleted_count raises ValidationError."""
        with pytest.raises(ValidationError):
            BulkDeleteResponse(deleted_count=-1)
