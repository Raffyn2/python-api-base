"""Tests for problem detail DTO.

**Feature: realistic-test-coverage**
**Validates: Requirements for application-layer-improvements-2025**
"""

import pytest
from pydantic import ValidationError

from application.common.dto.responses.problem_detail import ProblemDetail


class TestProblemDetail:
    """Tests for ProblemDetail (RFC 7807)."""

    def test_create_minimal(self) -> None:
        """Test creating minimal problem detail."""
        problem = ProblemDetail(title="Not Found", status=404)
        assert problem.title == "Not Found"
        assert problem.status == 404

    def test_default_type(self) -> None:
        """Test default type is about:blank."""
        problem = ProblemDetail(title="Error", status=500)
        assert problem.type == "about:blank"

    def test_custom_type(self) -> None:
        """Test custom type URI."""
        problem = ProblemDetail(
            type="https://api.example.com/errors/VALIDATION_ERROR",
            title="Validation Error",
            status=422,
        )
        assert problem.type == "https://api.example.com/errors/VALIDATION_ERROR"

    def test_detail_field(self) -> None:
        """Test detail field."""
        problem = ProblemDetail(
            title="Bad Request",
            status=400,
            detail="The request body is malformed",
        )
        assert problem.detail == "The request body is malformed"

    def test_default_detail_is_none(self) -> None:
        """Test default detail is None."""
        problem = ProblemDetail(title="Error", status=500)
        assert problem.detail is None

    def test_instance_field(self) -> None:
        """Test instance field."""
        problem = ProblemDetail(
            title="Not Found",
            status=404,
            instance="/api/v1/users/123",
        )
        assert problem.instance == "/api/v1/users/123"

    def test_default_instance_is_none(self) -> None:
        """Test default instance is None."""
        problem = ProblemDetail(title="Error", status=500)
        assert problem.instance is None

    def test_errors_field(self) -> None:
        """Test errors field with validation errors."""
        problem = ProblemDetail(
            title="Validation Error",
            status=422,
            errors=[
                {"field": "email", "message": "Invalid email format"},
                {"field": "age", "message": "Must be positive"},
            ],
        )
        assert len(problem.errors) == 2
        assert problem.errors[0]["field"] == "email"

    def test_default_errors_is_none(self) -> None:
        """Test default errors is None."""
        problem = ProblemDetail(title="Error", status=500)
        assert problem.errors is None

    def test_status_minimum(self) -> None:
        """Test status minimum validation."""
        with pytest.raises(ValidationError):
            ProblemDetail(title="Error", status=99)

    def test_status_maximum(self) -> None:
        """Test status maximum validation."""
        with pytest.raises(ValidationError):
            ProblemDetail(title="Error", status=600)

    def test_full_problem_detail(self) -> None:
        """Test full problem detail with all fields."""
        problem = ProblemDetail(
            type="https://api.example.com/errors/VALIDATION_ERROR",
            title="Validation Error",
            status=422,
            detail="Request validation failed",
            instance="/api/v1/items",
            errors=[
                {
                    "field": "price",
                    "message": "Price must be greater than 0",
                    "code": "value_error.number.not_gt",
                }
            ],
        )
        assert problem.type == "https://api.example.com/errors/VALIDATION_ERROR"
        assert problem.title == "Validation Error"
        assert problem.status == 422
        assert problem.detail == "Request validation failed"
        assert problem.instance == "/api/v1/items"
        assert len(problem.errors) == 1

    def test_serialization(self) -> None:
        """Test problem detail serialization."""
        problem = ProblemDetail(
            title="Not Found",
            status=404,
            detail="Resource not found",
        )
        data = problem.model_dump()
        
        assert data["type"] == "about:blank"
        assert data["title"] == "Not Found"
        assert data["status"] == 404
        assert data["detail"] == "Resource not found"

    def test_json_schema_has_examples(self) -> None:
        """Test JSON schema has examples."""
        schema = ProblemDetail.model_json_schema()
        assert "examples" in schema
