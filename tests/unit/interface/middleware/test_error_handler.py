"""Unit tests for error handler middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 9.1, 9.2**
"""

import importlib.util

# Import directly to avoid circular import issues
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError as PydanticValidationError

# Load the error_handler module directly
spec = importlib.util.spec_from_file_location(
    "error_handler_module", "src/interface/middleware/logging/error_handler.py"
)
error_handler_module = importlib.util.module_from_spec(spec)
sys.modules["error_handler_module"] = error_handler_module
spec.loader.exec_module(error_handler_module)

create_problem_detail = error_handler_module.create_problem_detail
app_exception_handler = error_handler_module.app_exception_handler
validation_exception_handler = error_handler_module.validation_exception_handler
unhandled_exception_handler = error_handler_module.unhandled_exception_handler
register_exception_handlers = error_handler_module.register_exception_handlers


class TestCreateProblemDetail:
    """Tests for create_problem_detail function."""

    def test_creates_rfc7807_response(self) -> None:
        """Test that problem detail follows RFC 7807 format."""
        request = MagicMock()
        request.url = "http://test.com/api/items"

        result = create_problem_detail(
            request=request,
            status=400,
            title="Bad Request",
            error_code="BAD_REQUEST",
            detail="Invalid input",
        )

        assert result["type"] == "https://api.example.com/errors/BAD_REQUEST"
        assert result["title"] == "Bad Request"
        assert result["status"] == 400
        assert result["detail"] == "Invalid input"
        assert result["instance"] == "http://test.com/api/items"

    def test_includes_errors_when_provided(self) -> None:
        """Test that errors list is included when provided."""
        request = MagicMock()
        request.url = "http://test.com/api/items"
        errors = [{"field": "name", "message": "required"}]

        result = create_problem_detail(
            request=request,
            status=422,
            title="Validation Error",
            error_code="VALIDATION_ERROR",
            errors=errors,
        )

        # ProblemDetail normalizes errors to ValidationErrorDetail format
        assert result["errors"] is not None
        assert len(result["errors"]) == 1
        assert result["errors"][0]["field"] == "name"
        assert result["errors"][0]["message"] == "required"

    def test_handles_none_detail(self) -> None:
        """Test that None detail is handled correctly."""
        request = MagicMock()
        request.url = "http://test.com/api/items"

        result = create_problem_detail(
            request=request,
            status=500,
            title="Internal Error",
            error_code="INTERNAL_ERROR",
            detail=None,
        )

        assert result["detail"] is None


class TestAppExceptionHandler:
    """Tests for app_exception_handler function."""

    @pytest.mark.asyncio
    async def test_handles_app_error(self) -> None:
        """Test handling of AppError exceptions."""
        from core.errors.base.domain_errors import AppError

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/api/items"
        request.state = MagicMock()
        request.state.request_id = "test-correlation-id"
        request.headers = {}

        exc = AppError(
            message="Item not found",
            error_code="NOT_FOUND",
            status_code=404,
        )

        with patch.object(error_handler_module, "logger"):
            response = await app_exception_handler(request, exc)

        assert response.status_code == 404
        assert b"NOT_FOUND" in response.body

    @pytest.mark.asyncio
    async def test_adds_www_authenticate_for_auth_error(self) -> None:
        """Test that WWW-Authenticate header is added for auth errors."""
        from core.errors.base.domain_errors import AuthenticationError

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/api/items"
        request.state = MagicMock()
        request.state.request_id = "test-id"
        request.headers = {}

        exc = AuthenticationError(
            message="Invalid token",
            scheme="Bearer",
        )

        with patch.object(error_handler_module, "logger"):
            response = await app_exception_handler(request, exc)

        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    @pytest.mark.asyncio
    async def test_adds_retry_after_for_rate_limit(self) -> None:
        """Test that Retry-After header is added for rate limit errors."""
        from core.errors.base.domain_errors import RateLimitExceededError

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/api/items"
        request.state = MagicMock()
        request.state.request_id = "test-id"
        request.headers = {}

        exc = RateLimitExceededError(
            retry_after=120,
            message="Too many requests",
        )

        with patch.object(error_handler_module, "logger"):
            response = await app_exception_handler(request, exc)

        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "120"


class TestUnhandledExceptionHandler:
    """Tests for unhandled_exception_handler function."""

    @pytest.mark.asyncio
    async def test_returns_generic_error(self) -> None:
        """Test that internal details are not exposed."""
        request = MagicMock()
        request.url = "http://test.com/api/items"
        request.method = "GET"
        request.state = MagicMock()
        request.state.request_id = "test-id"
        request.headers = {}

        exc = ValueError("Internal database error with sensitive info")

        with patch.object(error_handler_module, "logger"):
            response = await unhandled_exception_handler(request, exc)

        assert response.status_code == 500
        assert b"INTERNAL_ERROR" in response.body
        assert b"sensitive" not in response.body
        assert b"database" not in response.body

    @pytest.mark.asyncio
    async def test_logs_full_error(self) -> None:
        """Test that full error is logged for debugging."""
        request = MagicMock()
        request.url = "http://test.com/api/items"
        request.method = "GET"
        request.state = MagicMock()
        request.state.request_id = "test-correlation-id"
        request.headers = {}

        exc = ValueError("Internal error details")

        with patch.object(error_handler_module, "logger") as mock_logger:
            await unhandled_exception_handler(request, exc)

            mock_logger.exception.assert_called_once()
            call_kwargs = mock_logger.exception.call_args
            assert call_kwargs[1]["correlation_id"] == "test-correlation-id"


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler function."""

    @pytest.mark.asyncio
    async def test_formats_validation_errors(self) -> None:
        """Test that validation errors are properly formatted."""

        class TestModel(BaseModel):
            name: str
            age: int

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/api/items"
        request.state = MagicMock()
        request.state.request_id = "test-id"
        request.headers = {}

        try:
            TestModel(name=123, age="invalid")  # type: ignore
        except PydanticValidationError as exc:
            with patch.object(error_handler_module, "logger"):
                response = await validation_exception_handler(request, exc)

            assert response.status_code == 422
            assert b"VALIDATION_ERROR" in response.body


class TestRegisterExceptionHandlers:
    """Tests for register_exception_handlers function."""

    def test_registers_all_handlers(self) -> None:
        """Test that all exception handlers are registered."""
        app = MagicMock(spec=FastAPI)

        register_exception_handlers(app)

        assert app.add_exception_handler.call_count == 3


class TestIntegration:
    """Integration tests with FastAPI app."""

    @pytest.fixture()
    def app(self) -> FastAPI:
        """Create test FastAPI app with exception handlers."""
        from core.errors.base.domain_errors import AppError

        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/success")
        async def success_endpoint() -> dict:
            return {"status": "ok"}

        @app.get("/app-error")
        async def app_error_endpoint() -> dict:
            raise AppError(
                message="Test error",
                error_code="TEST_ERROR",
                status_code=400,
            )

        @app.get("/unhandled")
        async def unhandled_endpoint() -> dict:
            raise RuntimeError("Unexpected error")

        return app

    def test_success_response(self, app: FastAPI) -> None:
        """Test successful response."""
        client = TestClient(app)
        response = client.get("/success")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_app_error_response(self, app: FastAPI) -> None:
        """Test AppError response format."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/app-error")

        assert response.status_code == 400
        data = response.json()
        assert data["title"] == "Test Error"
        assert data["status"] == 400

    def test_unhandled_error_response(self, app: FastAPI) -> None:
        """Test unhandled error response format."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/unhandled")

        assert response.status_code == 500
        data = response.json()
        assert data["title"] == "Internal Server Error"
        assert "Unexpected" not in str(data)
