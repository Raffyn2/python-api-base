"""Tests for application/common/errors/auth - Auth error classes."""

import pytest

from src.application.common.errors.auth.forbidden_error import ForbiddenError
from src.application.common.errors.auth.unauthorized_error import UnauthorizedError


class TestForbiddenError:
    """Tests for ForbiddenError class."""

    def test_default_message(self):
        error = ForbiddenError()
        assert error.message == "Access denied"

    def test_custom_message(self):
        error = ForbiddenError("You cannot access this resource")
        assert error.message == "You cannot access this resource"

    def test_error_code(self):
        error = ForbiddenError()
        assert error.code == "FORBIDDEN"

    def test_is_exception(self):
        error = ForbiddenError()
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        with pytest.raises(ForbiddenError) as exc_info:
            raise ForbiddenError("No permission")
        assert exc_info.value.message == "No permission"

    def test_str_representation(self):
        error = ForbiddenError("Access denied to admin panel")
        assert "Access denied to admin panel" in str(error)


class TestUnauthorizedError:
    """Tests for UnauthorizedError class."""

    def test_default_message(self):
        error = UnauthorizedError()
        assert error.message == "Authentication required"

    def test_custom_message(self):
        error = UnauthorizedError("Invalid credentials")
        assert error.message == "Invalid credentials"

    def test_error_code(self):
        error = UnauthorizedError()
        assert error.code == "UNAUTHORIZED"

    def test_is_exception(self):
        error = UnauthorizedError()
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        with pytest.raises(UnauthorizedError) as exc_info:
            raise UnauthorizedError("Token expired")
        assert exc_info.value.message == "Token expired"

    def test_str_representation(self):
        error = UnauthorizedError("Please log in")
        assert "Please log in" in str(error)


class TestAuthErrorsDistinction:
    """Tests for distinguishing between auth errors."""

    def test_forbidden_vs_unauthorized(self):
        forbidden = ForbiddenError()
        unauthorized = UnauthorizedError()
        assert forbidden.code != unauthorized.code

    def test_catch_forbidden_specifically(self):
        try:
            raise ForbiddenError("No access")
        except ForbiddenError as e:
            assert e.code == "FORBIDDEN"

    def test_catch_unauthorized_specifically(self):
        try:
            raise UnauthorizedError("Not logged in")
        except UnauthorizedError as e:
            assert e.code == "UNAUTHORIZED"
