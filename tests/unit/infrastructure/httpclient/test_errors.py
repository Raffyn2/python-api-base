"""Tests for HTTP client error types.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from datetime import timedelta

from infrastructure.httpclient.errors import (
    CircuitBreakerError,
    HttpError,
    TimeoutError,
    ValidationError,
)


class TestHttpError:
    """Tests for HttpError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = HttpError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.request is None
        assert error.status_code is None
        assert error.response_body is None

    def test_create_with_request(self) -> None:
        """Test creating error with request context."""
        request = {"url": "/api/users", "method": "GET"}
        error = HttpError("Request failed", request=request)
        assert error.request == request

    def test_create_with_status_code(self) -> None:
        """Test creating error with status code."""
        error = HttpError("Not found", status_code=404)
        assert error.status_code == 404

    def test_create_with_response_body(self) -> None:
        """Test creating error with response body."""
        error = HttpError("Error", response_body='{"error": "not found"}')
        assert error.response_body == '{"error": "not found"}'

    def test_create_with_all_params(self) -> None:
        """Test creating error with all parameters."""
        request = {"url": "/api/items"}
        error = HttpError(
            "Server error",
            request=request,
            status_code=500,
            response_body='{"error": "internal"}',
        )
        assert str(error) == "Server error"
        assert error.request == request
        assert error.status_code == 500
        assert error.response_body == '{"error": "internal"}'

    def test_inherits_from_exception(self) -> None:
        """Test that HttpError inherits from Exception."""
        error = HttpError("test")
        assert isinstance(error, Exception)


class TestTimeoutError:
    """Tests for TimeoutError."""

    def test_create_timeout_error(self) -> None:
        """Test creating timeout error."""
        request = {"url": "/api/slow"}
        timeout = timedelta(seconds=30)
        error = TimeoutError(request, timeout)
        assert "30" in str(error)
        assert error.request == request
        assert error.timeout == timeout

    def test_timeout_message_format(self) -> None:
        """Test timeout error message format."""
        request = {"url": "/api/test"}
        timeout = timedelta(seconds=5)
        error = TimeoutError(request, timeout)
        assert "timed out" in str(error).lower()
        assert "5" in str(error)

    def test_timeout_with_milliseconds(self) -> None:
        """Test timeout with milliseconds."""
        request = {"url": "/api/test"}
        timeout = timedelta(milliseconds=500)
        error = TimeoutError(request, timeout)
        assert "0.5" in str(error)

    def test_inherits_from_http_error(self) -> None:
        """Test that TimeoutError inherits from HttpError."""
        request = {"url": "/api/test"}
        error = TimeoutError(request, timedelta(seconds=1))
        assert isinstance(error, HttpError)


class TestValidationError:
    """Tests for ValidationError."""

    def test_create_validation_error(self) -> None:
        """Test creating validation error."""

        class UserResponse:
            pass

        raw_response = {"name": 123}  # Invalid type
        validation_errors = [{"field": "name", "error": "must be string"}]

        error = ValidationError(
            "Validation failed",
            response_type=UserResponse,
            raw_response=raw_response,
            validation_errors=validation_errors,
        )

        assert str(error) == "Validation failed"
        assert error.response_type == UserResponse
        assert error.raw_response == raw_response
        assert error.validation_errors == validation_errors

    def test_validation_error_with_multiple_errors(self) -> None:
        """Test validation error with multiple validation errors."""

        class ItemResponse:
            pass

        validation_errors = [
            {"field": "name", "error": "required"},
            {"field": "price", "error": "must be positive"},
            {"field": "quantity", "error": "must be integer"},
        ]

        error = ValidationError(
            "Multiple validation errors",
            response_type=ItemResponse,
            raw_response={},
            validation_errors=validation_errors,
        )

        assert len(error.validation_errors) == 3

    def test_inherits_from_exception(self) -> None:
        """Test that ValidationError inherits from Exception."""

        class TestResponse:
            pass

        error = ValidationError(
            "test",
            response_type=TestResponse,
            raw_response={},
            validation_errors=[],
        )
        assert isinstance(error, Exception)


class TestCircuitBreakerError:
    """Tests for CircuitBreakerError."""

    def test_create_circuit_breaker_error(self) -> None:
        """Test creating circuit breaker error."""
        request = {"url": "/api/service"}
        error = CircuitBreakerError("Circuit is open", request=request)
        assert str(error) == "Circuit is open"
        assert error.request == request

    def test_inherits_from_http_error(self) -> None:
        """Test that CircuitBreakerError inherits from HttpError."""
        error = CircuitBreakerError("Circuit open")
        assert isinstance(error, HttpError)

    def test_with_status_code(self) -> None:
        """Test circuit breaker error with status code."""
        error = CircuitBreakerError(
            "Service unavailable",
            status_code=503,
        )
        assert error.status_code == 503
