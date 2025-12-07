"""Tests for API response DTO.

**Feature: realistic-test-coverage**
**Validates: Requirements for application-layer-improvements-2025**
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from application.common.dto.responses.api_response import ApiResponse


class TestApiResponse:
    """Tests for ApiResponse."""

    def test_create_with_data(self) -> None:
        """Test creating response with data."""
        response = ApiResponse[dict](data={"id": "123", "name": "Test"})
        assert response.data == {"id": "123", "name": "Test"}

    def test_default_message(self) -> None:
        """Test default message is Success."""
        response = ApiResponse[str](data="test")
        assert response.message == "Success"

    def test_default_status_code(self) -> None:
        """Test default status code is 200."""
        response = ApiResponse[str](data="test")
        assert response.status_code == 200

    def test_custom_message(self) -> None:
        """Test custom message."""
        response = ApiResponse[str](data="test", message="Created successfully")
        assert response.message == "Created successfully"

    def test_custom_status_code(self) -> None:
        """Test custom status code."""
        response = ApiResponse[str](data="test", status_code=201)
        assert response.status_code == 201

    def test_timestamp_auto_generated(self) -> None:
        """Test timestamp is auto-generated."""
        before = datetime.now(tz=UTC)
        response = ApiResponse[str](data="test")
        after = datetime.now(tz=UTC)
        
        assert response.timestamp >= before
        assert response.timestamp <= after

    def test_request_id(self) -> None:
        """Test request ID."""
        response = ApiResponse[str](data="test", request_id="req-123")
        assert response.request_id == "req-123"

    def test_default_request_id_is_none(self) -> None:
        """Test default request ID is None."""
        response = ApiResponse[str](data="test")
        assert response.request_id is None

    def test_status_code_minimum(self) -> None:
        """Test status code minimum validation."""
        with pytest.raises(ValidationError):
            ApiResponse[str](data="test", status_code=99)

    def test_status_code_maximum(self) -> None:
        """Test status code maximum validation."""
        with pytest.raises(ValidationError):
            ApiResponse[str](data="test", status_code=600)

    def test_with_list_data(self) -> None:
        """Test response with list data."""
        response = ApiResponse[list](data=[1, 2, 3])
        assert response.data == [1, 2, 3]

    def test_with_none_data(self) -> None:
        """Test response with None data."""
        response = ApiResponse[None](data=None)
        assert response.data is None

    def test_serialization(self) -> None:
        """Test response serialization."""
        response = ApiResponse[dict](
            data={"id": "123"},
            message="OK",
            status_code=200,
            request_id="req-456",
        )
        data = response.model_dump()
        
        assert data["data"] == {"id": "123"}
        assert data["message"] == "OK"
        assert data["status_code"] == 200
        assert data["request_id"] == "req-456"
        assert "timestamp" in data

    def test_from_attributes_config(self) -> None:
        """Test from_attributes config is set."""
        assert ApiResponse.model_config.get("from_attributes") is True
