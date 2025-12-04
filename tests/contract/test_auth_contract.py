"""Contract tests for Auth API.

Verifies the Auth API contract for authentication flows.

**Feature: contract-testing**
**Validates: Requirements 12.1, 12.2, 6.1**
"""

import pytest
from pydantic import BaseModel, Field


class TokenResponseContract(BaseModel):
    """Expected contract for token response (OAuth2 compliant)."""

    access_token: str = Field(..., min_length=1)
    token_type: str = Field(..., pattern=r"^[Bb]earer$")
    expires_in: int = Field(..., gt=0)
    refresh_token: str | None = None
    scope: str | None = None


class LoginRequestContract(BaseModel):
    """Expected contract for login request."""

    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=1)


class RefreshRequestContract(BaseModel):
    """Expected contract for refresh token request."""

    refresh_token: str = Field(..., min_length=1)


class ErrorResponseContract(BaseModel):
    """Expected contract for error response (RFC 7807)."""

    type: str
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str | None = None
    instance: str | None = None


class TestAuthContractSchema:
    """Auth endpoint contract tests."""

    def test_token_response_minimal(self) -> None:
        """Verify minimal token response matches contract."""
        data = {
            "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 1800,
        }
        response = TokenResponseContract.model_validate(data)
        assert response.token_type == "Bearer"
        assert response.expires_in == 1800

    def test_token_response_full(self) -> None:
        """Verify full token response matches contract."""
        data = {
            "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800,
            "refresh_token": "refresh_token_value",
            "scope": "read write",
        }
        response = TokenResponseContract.model_validate(data)
        assert response.refresh_token == "refresh_token_value"
        assert response.scope == "read write"

    def test_token_response_invalid_type(self) -> None:
        """Verify invalid token type fails contract."""
        data = {
            "access_token": "token",
            "token_type": "Basic",
            "expires_in": 1800,
        }
        with pytest.raises(ValueError):
            TokenResponseContract.model_validate(data)

    def test_token_response_invalid_expires(self) -> None:
        """Verify non-positive expires_in fails contract."""
        data = {
            "access_token": "token",
            "token_type": "Bearer",
            "expires_in": 0,
        }
        with pytest.raises(ValueError):
            TokenResponseContract.model_validate(data)

    def test_login_request_valid(self) -> None:
        """Verify valid login request matches contract."""
        data = {"email": "user@example.com", "password": "secret"}
        request = LoginRequestContract.model_validate(data)
        assert request.email == "user@example.com"

    def test_login_request_invalid_email(self) -> None:
        """Verify invalid email fails contract."""
        data = {"email": "not-an-email", "password": "secret"}
        with pytest.raises(ValueError):
            LoginRequestContract.model_validate(data)

    def test_refresh_request_valid(self) -> None:
        """Verify valid refresh request matches contract."""
        data = {"refresh_token": "refresh_token_value"}
        request = RefreshRequestContract.model_validate(data)
        assert request.refresh_token == "refresh_token_value"

    def test_error_response_401(self) -> None:
        """Verify 401 error response matches contract."""
        data = {
            "type": "https://httpstatuses.com/401",
            "title": "Unauthorized",
            "status": 401,
            "detail": "Invalid credentials",
        }
        response = ErrorResponseContract.model_validate(data)
        assert response.status == 401

    def test_error_response_429(self) -> None:
        """Verify 429 rate limit error matches contract."""
        data = {
            "type": "https://httpstatuses.com/429",
            "title": "Too Many Requests",
            "status": 429,
            "detail": "Rate limit exceeded",
            "instance": "/api/v1/auth/login",
        }
        response = ErrorResponseContract.model_validate(data)
        assert response.status == 429
        assert response.instance == "/api/v1/auth/login"


class TestAuthContractBackwardCompatibility:
    """Auth backward compatibility tests."""

    def test_token_response_oauth2_compliant(self) -> None:
        """Verify token response follows OAuth2 spec field names."""
        schema = TokenResponseContract.model_json_schema()
        properties = schema.get("properties", {})

        # OAuth2 required fields (snake_case per RFC 6749)
        assert "access_token" in properties
        assert "token_type" in properties
        assert "expires_in" in properties

    def test_error_response_rfc7807_compliant(self) -> None:
        """Verify error response follows RFC 7807 field names."""
        schema = ErrorResponseContract.model_json_schema()
        properties = schema.get("properties", {})

        # RFC 7807 fields
        assert "type" in properties
        assert "title" in properties
        assert "status" in properties
        assert "detail" in properties
        assert "instance" in properties
