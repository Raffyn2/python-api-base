"""Unit tests for HTTP constants.

Tests HttpStatus, ErrorCode, and ErrorMessages.
"""

import pytest

from core.errors.http.constants import ErrorCode, ErrorCodes, ErrorMessages, HttpStatus


class TestHttpStatus:
    """Tests for HttpStatus enum."""

    def test_success_codes(self) -> None:
        assert HttpStatus.OK == 200
        assert HttpStatus.CREATED == 201
        assert HttpStatus.ACCEPTED == 202
        assert HttpStatus.NO_CONTENT == 204

    def test_redirect_codes(self) -> None:
        assert HttpStatus.MOVED_PERMANENTLY == 301
        assert HttpStatus.FOUND == 302
        assert HttpStatus.NOT_MODIFIED == 304
        assert HttpStatus.TEMPORARY_REDIRECT == 307
        assert HttpStatus.PERMANENT_REDIRECT == 308

    def test_client_error_codes(self) -> None:
        assert HttpStatus.BAD_REQUEST == 400
        assert HttpStatus.UNAUTHORIZED == 401
        assert HttpStatus.FORBIDDEN == 403
        assert HttpStatus.NOT_FOUND == 404
        assert HttpStatus.METHOD_NOT_ALLOWED == 405
        assert HttpStatus.CONFLICT == 409
        assert HttpStatus.GONE == 410
        assert HttpStatus.UNPROCESSABLE_ENTITY == 422
        assert HttpStatus.TOO_MANY_REQUESTS == 429

    def test_server_error_codes(self) -> None:
        assert HttpStatus.INTERNAL_SERVER_ERROR == 500
        assert HttpStatus.NOT_IMPLEMENTED == 501
        assert HttpStatus.BAD_GATEWAY == 502
        assert HttpStatus.SERVICE_UNAVAILABLE == 503
        assert HttpStatus.GATEWAY_TIMEOUT == 504

    def test_is_int_enum(self) -> None:
        assert isinstance(HttpStatus.OK, int)
        assert HttpStatus.OK + 1 == 201


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_common_codes_exist(self) -> None:
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.UNAUTHORIZED == "UNAUTHORIZED"
        assert ErrorCode.FORBIDDEN == "FORBIDDEN"
        assert ErrorCode.CONFLICT == "CONFLICT"
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"

    def test_authentication_codes(self) -> None:
        assert ErrorCode.AUTHENTICATION_FAILED == "AUTHENTICATION_FAILED"
        assert ErrorCode.AUTHENTICATION_ERROR == "AUTHENTICATION_ERROR"
        assert ErrorCode.AUTHORIZATION_ERROR == "AUTHORIZATION_ERROR"

    def test_rate_limit_codes(self) -> None:
        assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"
        assert ErrorCode.RATE_LIMIT_EXCEEDED == "RATE_LIMIT_EXCEEDED"

    def test_is_string_enum(self) -> None:
        assert isinstance(ErrorCode.NOT_FOUND, str)
        assert ErrorCode.NOT_FOUND.upper() == "NOT_FOUND"

    def test_backward_compatibility_alias(self) -> None:
        assert ErrorCodes is ErrorCode
        assert ErrorCodes.NOT_FOUND == ErrorCode.NOT_FOUND


class TestErrorMessages:
    """Tests for ErrorMessages class."""

    def test_authentication_messages(self) -> None:
        assert "Invalid credentials" in ErrorMessages.INVALID_CREDENTIALS
        assert "expired" in ErrorMessages.TOKEN_EXPIRED
        assert "Invalid" in ErrorMessages.TOKEN_INVALID

    def test_authorization_messages(self) -> None:
        assert "denied" in ErrorMessages.FORBIDDEN.lower()
        assert "permissions" in ErrorMessages.INSUFFICIENT_PERMISSIONS.lower()

    def test_validation_messages(self) -> None:
        assert "Validation" in ErrorMessages.VALIDATION_FAILED
        assert "required" in ErrorMessages.REQUIRED_FIELD.lower()

    def test_resource_messages(self) -> None:
        assert "not found" in ErrorMessages.NOT_FOUND.lower()
        assert "exists" in ErrorMessages.ALREADY_EXISTS.lower()

    def test_not_found_method(self) -> None:
        msg = ErrorMessages.not_found("User", "123")
        assert "User" in msg
        assert "123" in msg
        assert "not found" in msg

    def test_validation_error_method(self) -> None:
        msg = ErrorMessages.validation_error("email", "invalid format")
        assert "email" in msg
        assert "invalid format" in msg

    def test_already_exists_method(self) -> None:
        msg = ErrorMessages.already_exists("User", "email", "test@example.com")
        assert "User" in msg
        assert "email" in msg
        assert "test@example.com" in msg

    def test_entity_not_found_template(self) -> None:
        template = ErrorMessages.ENTITY_NOT_FOUND
        msg = template.format(entity_type="Order", entity_id="456")
        assert "Order" in msg
        assert "456" in msg

    def test_permission_required_template(self) -> None:
        template = ErrorMessages.PERMISSION_REQUIRED
        msg = template.format(permission="admin:write")
        assert "admin:write" in msg

    def test_rate_limit_template(self) -> None:
        template = ErrorMessages.RATE_LIMIT_EXCEEDED
        msg = template.format(retry_after=60)
        assert "60" in msg

    def test_business_rule_template(self) -> None:
        template = ErrorMessages.BUSINESS_RULE_VIOLATED
        msg = template.format(rule="max_items", message="Cannot exceed 100 items")
        assert "max_items" in msg
        assert "Cannot exceed 100 items" in msg

