"""Unit tests for RFC 7807 exception handlers.

**Task: Phase 1 - Core Layer Tests**
**Requirements: 3.3**
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.errors.http.exception_handlers import (
    _create_problem_response,
    _get_correlation_id,
    generic_exception_handler,
    http_exception_handler,
    pydantic_exception_handler,
    setup_exception_handlers,
    validation_exception_handler,
)
from core.errors.http.problem_details import ProblemDetail


class TestGetCorrelationId:
    """Tests for _get_correlation_id helper."""

    def test_from_header(self) -> None:
        """Should extract correlation ID from header."""
        request = MagicMock()
        request.headers = {"X-Correlation-ID": "test-123"}
        request.state = MagicMock(spec=[])

        result = _get_correlation_id(request)

        assert result == "test-123"

    def test_from_state(self) -> None:
        """Should extract correlation ID from request state."""
        request = MagicMock()
        request.headers = {}
        request.state.correlation_id = "state-456"

        result = _get_correlation_id(request)

        assert result == "state-456"

    def test_header_takes_precedence(self) -> None:
        """Header should take precedence over state."""
        request = MagicMock()
        request.headers = {"X-Correlation-ID": "header-123"}
        request.state.correlation_id = "state-456"

        result = _get_correlation_id(request)

        assert result == "header-123"

    def test_returns_none_when_not_found(self) -> None:
        """Should return None when no correlation ID found."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])

        result = _get_correlation_id(request)

        assert result is None


class TestCreateProblemResponse:
    """Tests for _create_problem_response helper."""

    def test_creates_json_response(self) -> None:
        """Should create JSONResponse with problem details."""
        problem = ProblemDetail.from_status(
            status=404,
            detail="Not found",
        )

        response = _create_problem_response(problem)

        assert response.status_code == 404
        assert "application/problem+json" in response.headers["content-type"]

    def test_includes_custom_headers(self) -> None:
        """Should include custom headers."""
        problem = ProblemDetail.from_status(status=401, detail="Unauthorized")

        response = _create_problem_response(
            problem,
            headers={"WWW-Authenticate": "Bearer"},
        )

        assert response.headers.get("WWW-Authenticate") == "Bearer"


class TestHttpExceptionHandler:
    """Tests for http_exception_handler."""

    @pytest.mark.asyncio
    async def test_handles_http_exception(self) -> None:
        """Should handle HTTP exception with RFC 7807 format."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/users/123"

        exc = StarletteHTTPException(status_code=404, detail="User not found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        assert "application/problem+json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_includes_correlation_id(self) -> None:
        """Should include correlation ID in response."""
        request = MagicMock()
        request.headers = {"X-Correlation-ID": "corr-123"}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/test"

        exc = StarletteHTTPException(status_code=500, detail="Error")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_preserves_exception_headers(self) -> None:
        """Should preserve headers from exception."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/test"

        exc = StarletteHTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

        response = await http_exception_handler(request, exc)

        assert response.headers.get("WWW-Authenticate") == "Bearer"


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_handles_validation_error(self) -> None:
        """Should handle validation error with RFC 7807 format."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/users"

        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "email"),
                    "msg": "Invalid email format",
                    "type": "value_error",
                }
            ]
        )

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422
        assert "application/problem+json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_handles_multiple_errors(self) -> None:
        """Should handle multiple validation errors."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/users"

        exc = RequestValidationError(
            errors=[
                {"loc": ("body", "email"), "msg": "Required", "type": "missing"},
                {"loc": ("body", "password"), "msg": "Too short", "type": "string_too_short"},
            ]
        )

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422


class TestGenericExceptionHandler:
    """Tests for generic_exception_handler."""

    @pytest.mark.asyncio
    async def test_handles_generic_exception(self) -> None:
        """Should handle generic exception safely."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/test"
        request.method = "GET"

        exc = Exception("Internal error details")

        response = await generic_exception_handler(request, exc)

        assert response.status_code == 500
        assert "application/problem+json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_does_not_expose_sensitive_details(self) -> None:
        """Should not expose sensitive error details."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock(spec=[])
        request.url.path = "/api/test"
        request.method = "POST"

        exc = Exception("Database password: secret123")

        response = await generic_exception_handler(request, exc)

        # Response body should not contain sensitive info
        assert response.status_code == 500


class TestSetupExceptionHandlers:
    """Tests for setup_exception_handlers."""

    def test_registers_handlers(self) -> None:
        """Should register all exception handlers."""
        app = MagicMock(spec=FastAPI)

        setup_exception_handlers(app)

        assert app.add_exception_handler.call_count == 4
