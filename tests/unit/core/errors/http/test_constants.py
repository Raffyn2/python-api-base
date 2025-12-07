"""Tests for core/errors/http/constants.py - HTTP constants."""

import pytest

from src.core.errors.http.constants import (
    ErrorCode,
    ErrorCodes,
    ErrorMessages,
    HttpStatus,
)


class TestHttpStatus:
    """Tests for HttpStatus enum."""

    # 2xx Success
    def test_ok_value(self):
        assert HttpStatus.OK == 200

    def test_created_value(self):
        assert HttpStatus.CREATED == 201

    def test_accepted_value(self):
        assert HttpStatus.ACCEPTED == 202

    def test_no_content_value(self):
        assert HttpStatus.NO_CONTENT == 204

    # 3xx Redirection
    def test_moved_permanently_value(self):
        assert HttpStatus.MOVED_PERMANENTLY == 301

    def test_found_value(self):
        assert HttpStatus.FOUND == 302

    def test_not_modified_value(self):
        assert HttpStatus.NOT_MODIFIED == 304

    def test_temporary_redirect_value(self):
        assert HttpStatus.TEMPORARY_REDIRECT == 307

    def test_permanent_redirect_value(self):
        assert HttpStatus.PERMANENT_REDIRECT == 308

    # 4xx Client Errors
    def test_bad_request_value(self):
        assert HttpStatus.BAD_REQUEST == 400

    def test_unauthorized_value(self):
        assert HttpStatus.UNAUTHORIZED == 401

    def test_forbidden_value(self):
        assert HttpStatus.FORBIDDEN == 403

    def test_not_found_value(self):
        assert HttpStatus.NOT_FOUND == 404

    def test_method_not_allowed_value(self):
        assert HttpStatus.METHOD_NOT_ALLOWED == 405

    def test_conflict_value(self):
        assert HttpStatus.CONFLICT == 409

    def test_gone_value(self):
        assert HttpStatus.GONE == 410

    def test_unprocessable_entity_value(self):
        assert HttpStatus.UNPROCESSABLE_ENTITY == 422

    def test_too_many_requests_value(self):
        assert HttpStatus.TOO_MANY_REQUESTS == 429

    # 5xx Server Errors
    def test_internal_server_error_value(self):
        assert HttpStatus.INTERNAL_SERVER_ERROR == 500

    def test_not_implemented_value(self):
        assert HttpStatus.NOT_IMPLEMENTED == 501

    def test_bad_gateway_value(self):
        assert HttpStatus.BAD_GATEWAY == 502

    def test_service_unavailable_value(self):
        assert HttpStatus.SERVICE_UNAVAILABLE == 503

    def test_gateway_timeout_value(self):
        assert HttpStatus.GATEWAY_TIMEOUT == 504

    def test_is_int_enum(self):
        assert isinstance(HttpStatus.OK, int)
        assert HttpStatus.OK == 200

    def test_all_members_count(self):
        assert len(HttpStatus) == 23

    def test_from_int(self):
        assert HttpStatus(200) == HttpStatus.OK
        assert HttpStatus(404) == HttpStatus.NOT_FOUND

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            HttpStatus(999)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_not_found_value(self):
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"

    def test_entity_not_found_value(self):
        assert ErrorCode.ENTITY_NOT_FOUND.value == "ENTITY_NOT_FOUND"

    def test_validation_error_value(self):
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"

    def test_unauthorized_value(self):
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"

    def test_forbidden_value(self):
        assert ErrorCode.FORBIDDEN.value == "FORBIDDEN"

    def test_conflict_value(self):
        assert ErrorCode.CONFLICT.value == "CONFLICT"

    def test_internal_error_value(self):
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"

    def test_timeout_value(self):
        assert ErrorCode.TIMEOUT.value == "TIMEOUT"

    def test_rate_limited_value(self):
        assert ErrorCode.RATE_LIMITED.value == "RATE_LIMITED"

    def test_rate_limit_exceeded_value(self):
        assert ErrorCode.RATE_LIMIT_EXCEEDED.value == "RATE_LIMIT_EXCEEDED"

    def test_bad_request_value(self):
        assert ErrorCode.BAD_REQUEST.value == "BAD_REQUEST"

    def test_service_unavailable_value(self):
        assert ErrorCode.SERVICE_UNAVAILABLE.value == "SERVICE_UNAVAILABLE"

    def test_network_error_value(self):
        assert ErrorCode.NETWORK_ERROR.value == "NETWORK_ERROR"

    def test_configuration_error_value(self):
        assert ErrorCode.CONFIGURATION_ERROR.value == "CONFIGURATION_ERROR"

    def test_authentication_failed_value(self):
        assert ErrorCode.AUTHENTICATION_FAILED.value == "AUTHENTICATION_FAILED"

    def test_authentication_error_value(self):
        assert ErrorCode.AUTHENTICATION_ERROR.value == "AUTHENTICATION_ERROR"

    def test_authorization_error_value(self):
        assert ErrorCode.AUTHORIZATION_ERROR.value == "AUTHORIZATION_ERROR"

    def test_permission_denied_value(self):
        assert ErrorCode.PERMISSION_DENIED.value == "PERMISSION_DENIED"

    def test_resource_exhausted_value(self):
        assert ErrorCode.RESOURCE_EXHAUSTED.value == "RESOURCE_EXHAUSTED"

    def test_precondition_failed_value(self):
        assert ErrorCode.PRECONDITION_FAILED.value == "PRECONDITION_FAILED"

    def test_unsupported_operation_value(self):
        assert ErrorCode.UNSUPPORTED_OPERATION.value == "UNSUPPORTED_OPERATION"

    def test_method_not_found_value(self):
        assert ErrorCode.METHOD_NOT_FOUND.value == "METHOD_NOT_FOUND"

    def test_invalid_params_value(self):
        assert ErrorCode.INVALID_PARAMS.value == "INVALID_PARAMS"

    def test_parse_error_value(self):
        assert ErrorCode.PARSE_ERROR.value == "PARSE_ERROR"

    def test_business_rule_violation_value(self):
        assert ErrorCode.BUSINESS_RULE_VIOLATION.value == "BUSINESS_RULE_VIOLATION"

    def test_is_string_enum(self):
        assert isinstance(ErrorCode.NOT_FOUND, str)
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"

    def test_from_string(self):
        assert ErrorCode("NOT_FOUND") == ErrorCode.NOT_FOUND
        assert ErrorCode("VALIDATION_ERROR") == ErrorCode.VALIDATION_ERROR


class TestErrorCodesAlias:
    """Tests for ErrorCodes backward compatibility alias."""

    def test_alias_is_same_as_error_code(self):
        assert ErrorCodes is ErrorCode

    def test_alias_members_accessible(self):
        assert ErrorCodes.NOT_FOUND == ErrorCode.NOT_FOUND
        assert ErrorCodes.VALIDATION_ERROR == ErrorCode.VALIDATION_ERROR


class TestErrorMessages:
    """Tests for ErrorMessages class."""

    # Authentication errors
    def test_invalid_credentials(self):
        assert ErrorMessages.INVALID_CREDENTIALS == "Invalid credentials provided"

    def test_token_expired(self):
        assert ErrorMessages.TOKEN_EXPIRED == "Authentication token has expired"

    def test_token_invalid(self):
        assert ErrorMessages.TOKEN_INVALID == "Invalid authentication token"

    def test_unauthorized(self):
        assert ErrorMessages.UNAUTHORIZED == "Authentication required"

    def test_authentication_required(self):
        assert ErrorMessages.AUTHENTICATION_REQUIRED == "Authentication required"

    # Authorization errors
    def test_forbidden(self):
        assert ErrorMessages.FORBIDDEN == "Access denied"

    def test_insufficient_permissions(self):
        assert (
            ErrorMessages.INSUFFICIENT_PERMISSIONS
            == "Insufficient permissions for this operation"
        )

    def test_permission_denied(self):
        assert ErrorMessages.PERMISSION_DENIED == "Permission denied"

    def test_permission_required(self):
        assert ErrorMessages.PERMISSION_REQUIRED == "Permission '{permission}' is required"

    # Validation errors
    def test_validation_failed(self):
        assert ErrorMessages.VALIDATION_FAILED == "Validation failed"

    def test_required_field(self):
        assert ErrorMessages.REQUIRED_FIELD == "This field is required"

    def test_invalid_format(self):
        assert ErrorMessages.INVALID_FORMAT == "Invalid format"

    def test_invalid_value(self):
        assert ErrorMessages.INVALID_VALUE == "Invalid value"

    # Resource errors
    def test_not_found(self):
        assert ErrorMessages.NOT_FOUND == "Resource not found"

    def test_entity_not_found_template(self):
        assert (
            ErrorMessages.ENTITY_NOT_FOUND
            == "{entity_type} with id '{entity_id}' not found"
        )

    def test_already_exists(self):
        assert ErrorMessages.ALREADY_EXISTS == "Resource already exists"

    def test_conflict(self):
        assert ErrorMessages.CONFLICT == "Resource conflict"

    def test_conflict_resource_template(self):
        assert (
            ErrorMessages.CONFLICT_RESOURCE
            == "{resource_type} with id '{resource_id}' already exists"
        )

    # Business rules
    def test_business_rule_violated_template(self):
        assert (
            ErrorMessages.BUSINESS_RULE_VIOLATED
            == "Business rule '{rule}' violated: {message}"
        )

    # Rate limiting
    def test_rate_limit_exceeded_template(self):
        assert (
            ErrorMessages.RATE_LIMIT_EXCEEDED
            == "Rate limit exceeded. Retry after {retry_after} seconds"
        )

    # Server errors
    def test_internal_error(self):
        assert ErrorMessages.INTERNAL_ERROR == "An internal error occurred"

    def test_service_unavailable(self):
        assert ErrorMessages.SERVICE_UNAVAILABLE == "Service temporarily unavailable"

    def test_timeout(self):
        assert ErrorMessages.TIMEOUT == "Operation timed out"


class TestErrorMessagesClassMethods:
    """Tests for ErrorMessages class methods."""

    def test_not_found_method(self):
        result = ErrorMessages.not_found("User", "123")
        assert result == "User with id '123' not found"

    def test_not_found_method_different_resource(self):
        result = ErrorMessages.not_found("Order", "abc-456")
        assert result == "Order with id 'abc-456' not found"

    def test_validation_error_method(self):
        result = ErrorMessages.validation_error("email", "must be a valid email")
        assert result == "Validation failed for field 'email': must be a valid email"

    def test_validation_error_method_different_field(self):
        result = ErrorMessages.validation_error("age", "must be positive")
        assert result == "Validation failed for field 'age': must be positive"

    def test_already_exists_method(self):
        result = ErrorMessages.already_exists("User", "email", "test@example.com")
        assert result == "User with email 'test@example.com' already exists"

    def test_already_exists_method_different_resource(self):
        result = ErrorMessages.already_exists("Product", "sku", "SKU-123")
        assert result == "Product with sku 'SKU-123' already exists"


class TestHttpStatusCategories:
    """Tests for HTTP status code categories."""

    def test_success_codes_range(self):
        success_codes = [
            HttpStatus.OK,
            HttpStatus.CREATED,
            HttpStatus.ACCEPTED,
            HttpStatus.NO_CONTENT,
        ]
        for code in success_codes:
            assert 200 <= code < 300

    def test_redirect_codes_range(self):
        redirect_codes = [
            HttpStatus.MOVED_PERMANENTLY,
            HttpStatus.FOUND,
            HttpStatus.NOT_MODIFIED,
            HttpStatus.TEMPORARY_REDIRECT,
            HttpStatus.PERMANENT_REDIRECT,
        ]
        for code in redirect_codes:
            assert 300 <= code < 400

    def test_client_error_codes_range(self):
        client_error_codes = [
            HttpStatus.BAD_REQUEST,
            HttpStatus.UNAUTHORIZED,
            HttpStatus.FORBIDDEN,
            HttpStatus.NOT_FOUND,
            HttpStatus.METHOD_NOT_ALLOWED,
            HttpStatus.CONFLICT,
            HttpStatus.GONE,
            HttpStatus.UNPROCESSABLE_ENTITY,
            HttpStatus.TOO_MANY_REQUESTS,
        ]
        for code in client_error_codes:
            assert 400 <= code < 500

    def test_server_error_codes_range(self):
        server_error_codes = [
            HttpStatus.INTERNAL_SERVER_ERROR,
            HttpStatus.NOT_IMPLEMENTED,
            HttpStatus.BAD_GATEWAY,
            HttpStatus.SERVICE_UNAVAILABLE,
            HttpStatus.GATEWAY_TIMEOUT,
        ]
        for code in server_error_codes:
            assert 500 <= code < 600


class TestErrorCodeCategories:
    """Tests for error code categories."""

    def test_authentication_related_codes(self):
        auth_codes = [
            ErrorCode.UNAUTHORIZED,
            ErrorCode.AUTHENTICATION_FAILED,
            ErrorCode.AUTHENTICATION_ERROR,
        ]
        for code in auth_codes:
            assert "AUTH" in code.value or code.value == "UNAUTHORIZED"

    def test_authorization_related_codes(self):
        authz_codes = [
            ErrorCode.FORBIDDEN,
            ErrorCode.AUTHORIZATION_ERROR,
            ErrorCode.PERMISSION_DENIED,
        ]
        for code in authz_codes:
            assert code.value in [
                "FORBIDDEN",
                "AUTHORIZATION_ERROR",
                "PERMISSION_DENIED",
            ]

    def test_resource_related_codes(self):
        resource_codes = [
            ErrorCode.NOT_FOUND,
            ErrorCode.ENTITY_NOT_FOUND,
            ErrorCode.CONFLICT,
            ErrorCode.RESOURCE_EXHAUSTED,
        ]
        for code in resource_codes:
            assert code in ErrorCode


class TestEnumComparisons:
    """Tests for enum comparisons."""

    def test_http_status_int_comparison(self):
        assert HttpStatus.OK == 200
        assert HttpStatus.NOT_FOUND == 404
        assert HttpStatus.OK < HttpStatus.NOT_FOUND

    def test_error_code_string_comparison(self):
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"

    def test_http_status_arithmetic(self):
        assert HttpStatus.OK + 1 == 201
        assert HttpStatus.NOT_FOUND - 4 == 400
