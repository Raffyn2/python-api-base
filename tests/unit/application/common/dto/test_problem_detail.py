"""Unit tests for ProblemDetail DTO.

Tests RFC 7807 Problem Details response format.
"""

import pytest
from pydantic import ValidationError

from application.common.dto import ProblemDetail


class TestProblemDetail:
    """Tests for ProblemDetail DTO."""

    def test_basic_creation(self) -> None:
        """Test basic ProblemDetail creation."""
        detail = ProblemDetail(
            title="Not Found",
            status=404,
        )
        assert detail.title == "Not Found"
        assert detail.status == 404
        assert detail.type == "about:blank"

    def test_with_all_fields(self) -> None:
        """Test ProblemDetail with all fields."""
        detail = ProblemDetail(
            type="https://api.example.com/errors/VALIDATION_ERROR",
            title="Validation Error",
            status=422,
            detail="Request validation failed",
            instance="/api/v1/items",
            errors=[{"field": "price", "message": "Must be positive"}],
        )
        assert detail.type == "https://api.example.com/errors/VALIDATION_ERROR"
        assert detail.title == "Validation Error"
        assert detail.status == 422
        assert detail.detail == "Request validation failed"
        assert detail.instance == "/api/v1/items"
        assert len(detail.errors) == 1

    def test_default_type(self) -> None:
        """Test default type is about:blank."""
        detail = ProblemDetail(title="Error", status=500)
        assert detail.type == "about:blank"

    def test_optional_detail(self) -> None:
        """Test detail field is optional."""
        detail = ProblemDetail(title="Error", status=500)
        assert detail.detail is None

    def test_optional_instance(self) -> None:
        """Test instance field is optional."""
        detail = ProblemDetail(title="Error", status=500)
        assert detail.instance is None

    def test_optional_errors(self) -> None:
        """Test errors field is optional."""
        detail = ProblemDetail(title="Error", status=500)
        assert detail.errors is None

    def test_invalid_status_too_low(self) -> None:
        """Test status code below 100 is invalid."""
        with pytest.raises(ValidationError):
            ProblemDetail(title="Error", status=99)

    def test_invalid_status_too_high(self) -> None:
        """Test status code above 599 is invalid."""
        with pytest.raises(ValidationError):
            ProblemDetail(title="Error", status=600)

    def test_client_error_status(self) -> None:
        """Test 4xx client error status codes."""
        for status in [400, 401, 403, 404, 409, 422, 429]:
            detail = ProblemDetail(title="Client Error", status=status)
            assert detail.status == status

    def test_server_error_status(self) -> None:
        """Test 5xx server error status codes."""
        for status in [500, 501, 502, 503, 504]:
            detail = ProblemDetail(title="Server Error", status=status)
            assert detail.status == status

    def test_multiple_errors(self) -> None:
        """Test ProblemDetail with multiple validation errors."""
        errors = [
            {"field": "email", "message": "Invalid format", "code": "invalid_email"},
            {"field": "age", "message": "Must be positive", "code": "min_value"},
            {"field": "name", "message": "Required", "code": "required"},
        ]
        detail = ProblemDetail(
            title="Validation Error",
            status=422,
            errors=errors,
        )
        assert len(detail.errors) == 3

    def test_serialization(self) -> None:
        """Test ProblemDetail serialization to dict."""
        detail = ProblemDetail(
            type="https://api.example.com/errors/NOT_FOUND",
            title="Not Found",
            status=404,
            detail="User not found",
            instance="/api/v1/users/123",
        )
        data = detail.model_dump()
        assert data["type"] == "https://api.example.com/errors/NOT_FOUND"
        assert data["title"] == "Not Found"
        assert data["status"] == 404

    def test_json_serialization(self) -> None:
        """Test ProblemDetail JSON serialization."""
        detail = ProblemDetail(
            title="Error",
            status=500,
        )
        json_str = detail.model_dump_json()
        assert "Error" in json_str
        assert "500" in json_str
