"""Unit tests for core/errors/http/constants.py.

Tests HTTP status codes and error code constants.

**Task 4.2: Create tests for error constants**
**Requirements: 3.3**
"""

from core.errors.http.constants import ErrorCode, ErrorCodes, ErrorMessages, HttpStatus


class TestHttpStatus:
    """Tests for HttpStatus enum."""

    def test_success_codes(self) -> None:
        """Test 2xx success status codes."""
        assert HttpStatus.OK == 200
        assert HttpStatus.CREATED == 201
        assert HttpStatus.ACCEPTED == 202
        assert HttpStatus.NO_CONTENT == 204

    def test_client_error_codes(self) -> None:
        """Test 4xx client error status codes."""
        assert HttpStatus.BAD_REQUEST == 400
        assert HttpStatus.UNAUTHORIZED == 401
        assert HttpStatus.FORBIDDEN == 403
        assert HttpStatus.NOT_FOUND == 404
        assert HttpStatus.CONFLICT == 409
        assert HttpStatus.UNPROCESSABLE_ENTITY == 422
        assert HttpStatus.TOO_MANY_REQUESTS == 429

    def test_server_error_codes(self) -> None:
        """Test 5xx server error status codes."""
        assert HttpStatus.INTERNAL_SERVER_ERROR == 500
        assert HttpStatus.SERVICE_UNAVAILABLE == 503

    def test_is_int_enum(self) -> None:
        """Test HttpStatus values are integers."""
        assert isinstance(HttpStatus.OK.value, int)
        assert HttpStatus.OK + 1 == 201


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_common_error_codes(self) -> None:
        """Test common error codes exist."""
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.UNAUTHORIZED == "UNAUTHORIZED"
        assert ErrorCode.FORBIDDEN == "FORBIDDEN"
        assert ErrorCode.CONFLICT == "CONFLICT"

    def test_error_codes_alias(self) -> None:
        """Test ErrorCodes is alias for ErrorCode."""
        assert ErrorCodes is ErrorCode


class TestErrorMessages:
    """Tests for ErrorMessages class."""

    def test_authentication_messages(self) -> None:
        """Test authentication error messages."""
        assert "credentials" in ErrorMessages.INVALID_CREDENTIALS.lower()
        assert "expired" in ErrorMessages.TOKEN_EXPIRED.lower()
        assert "required" in ErrorMessages.AUTHENTICATION_REQUIRED.lower()

    def test_authorization_messages(self) -> None:
        """Test authorization error messages."""
        assert "denied" in ErrorMessages.PERMISSION_DENIED.lower()

    def test_validation_messages(self) -> None:
        """Test validation error messages."""
        assert "failed" in ErrorMessages.VALIDATION_FAILED.lower()
        assert "required" in ErrorMessages.REQUIRED_FIELD.lower()

    def test_not_found_method(self) -> None:
        """Test not_found class method."""
        msg = ErrorMessages.not_found("User", "123")
        assert "User" in msg
        assert "123" in msg

    def test_validation_error_method(self) -> None:
        """Test validation_error class method."""
        msg = ErrorMessages.validation_error("email", "Invalid format")
        assert "email" in msg
        assert "Invalid format" in msg

    def test_already_exists_method(self) -> None:
        """Test already_exists class method."""
        msg = ErrorMessages.already_exists("User", "email", "test@example.com")
        assert "User" in msg
        assert "email" in msg
        assert "test@example.com" in msg

    def test_entity_not_found_format(self) -> None:
        """Test ENTITY_NOT_FOUND message formatting."""
        msg = ErrorMessages.ENTITY_NOT_FOUND.format(entity_type="Order", entity_id="456")
        assert "Order" in msg
        assert "456" in msg

    def test_business_rule_violated_format(self) -> None:
        """Test BUSINESS_RULE_VIOLATED message formatting."""
        msg = ErrorMessages.BUSINESS_RULE_VIOLATED.format(rule="MAX_ITEMS", message="Limit exceeded")
        assert "MAX_ITEMS" in msg
        assert "Limit exceeded" in msg

    def test_rate_limit_exceeded_format(self) -> None:
        """Test RATE_LIMIT_EXCEEDED message formatting."""
        msg = ErrorMessages.RATE_LIMIT_EXCEEDED.format(retry_after=60)
        assert "60" in msg
