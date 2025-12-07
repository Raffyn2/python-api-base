"""Unit tests for generic error classes.

Tests ErrorContext, DomainError, ApplicationError, InfrastructureError,
and map_error function.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from core.errors.shared.generic_errors import (
    ApplicationError,
    DomainError,
    ErrorContext,
    InfrastructureError,
    map_error,
)


class TestErrorContext:
    """Tests for ErrorContext dataclass."""

    def test_default_values(self) -> None:
        """Test default context values."""
        ctx: ErrorContext[None] = ErrorContext()
        
        assert ctx.correlation_id is not None
        assert ctx.timestamp is not None
        assert ctx.context_data is None
        assert ctx.request_path is None
        assert ctx.operation is None

    def test_with_context_data(self) -> None:
        """Test context with typed data."""
        ctx: ErrorContext[dict] = ErrorContext(
            context_data={"user_id": "123", "action": "update"}
        )
        
        assert ctx.context_data == {"user_id": "123", "action": "update"}

    def test_with_request_info(self) -> None:
        """Test context with request info."""
        ctx: ErrorContext[None] = ErrorContext(
            request_path="/api/users/123",
            operation="UpdateUser",
        )
        
        assert ctx.request_path == "/api/users/123"
        assert ctx.operation == "UpdateUser"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        ctx: ErrorContext[str] = ErrorContext(
            context_data="test-data",
            request_path="/api/test",
            operation="TestOp",
        )
        
        result = ctx.to_dict()
        
        assert "correlation_id" in result
        assert "timestamp" in result
        assert result["context_data"] == "test-data"
        assert result["request_path"] == "/api/test"
        assert result["operation"] == "TestOp"

    def test_immutability(self) -> None:
        """Test context is immutable."""
        ctx: ErrorContext[None] = ErrorContext()
        
        with pytest.raises(AttributeError):
            ctx.correlation_id = "new-id"  # type: ignore[misc]


class TestDomainError:
    """Tests for DomainError class."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""
        error: DomainError[None] = DomainError(message="Test error")
        
        assert error.message == "Test error"
        assert error.error_code == "DOMAIN_ERROR"
        assert error.context is None
        assert str(error) == "Test error"

    def test_with_error_code(self) -> None:
        """Test error with custom code."""
        error: DomainError[None] = DomainError(
            message="User not found",
            error_code="USER_NOT_FOUND",
        )
        
        assert error.error_code == "USER_NOT_FOUND"

    def test_with_typed_context(self) -> None:
        """Test error with typed context."""
        @dataclass
        class UserContext:
            user_id: str
            action: str

        ctx = UserContext(user_id="123", action="update")
        error: DomainError[UserContext] = DomainError(
            message="User action failed",
            context=ctx,
        )
        
        assert error.context is not None
        assert error.context.user_id == "123"
        assert error.context.action == "update"

    def test_with_cause(self) -> None:
        """Test error with cause."""
        cause = ValueError("Original error")
        error: DomainError[None] = DomainError(
            message="Wrapped error",
            cause=cause,
        )
        
        assert error._cause is cause
        assert error.__cause__ is cause

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        error: DomainError[str] = DomainError(
            message="Test error",
            error_code="TEST_ERROR",
            context="test-context",
        )
        
        result = error.to_dict()
        
        assert result["type"] == "DomainError"
        assert result["message"] == "Test error"
        assert result["error_code"] == "TEST_ERROR"
        assert result["context"] == "test-context"

    def test_to_dict_with_cause(self) -> None:
        """Test serialization includes cause."""
        cause = ValueError("Original")
        error: DomainError[None] = DomainError(
            message="Wrapped",
            cause=cause,
        )
        
        result = error.to_dict()
        
        assert "cause" in result
        assert result["cause"] == "Original"


class TestApplicationError:
    """Tests for ApplicationError class."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""
        error: ApplicationError[None] = ApplicationError(
            message="Use case failed",
            operation="CreateUser",
        )
        
        assert error.message == "Use case failed"
        assert error.operation == "CreateUser"
        assert error.error_code == "APPLICATION_ERROR"

    def test_with_context(self) -> None:
        """Test error with typed context."""
        @dataclass
        class OpContext:
            use_case: str
            input_data: dict

        ctx = OpContext(use_case="CreateUser", input_data={"name": "John"})
        error: ApplicationError[OpContext] = ApplicationError(
            message="Validation failed",
            operation="CreateUser",
            context=ctx,
        )
        
        assert error.context is not None
        assert error.context.use_case == "CreateUser"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        error: ApplicationError[None] = ApplicationError(
            message="Failed",
            operation="TestOp",
            error_code="CUSTOM_ERROR",
        )
        
        result = error.to_dict()
        
        assert result["type"] == "ApplicationError"
        assert result["operation"] == "TestOp"
        assert result["error_code"] == "CUSTOM_ERROR"


class TestInfrastructureError:
    """Tests for InfrastructureError class."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""
        error: InfrastructureError[None] = InfrastructureError(
            message="Connection failed",
            service="PostgreSQL",
        )
        
        assert error.message == "Connection failed"
        assert error.service == "PostgreSQL"
        assert error.error_code == "INFRASTRUCTURE_ERROR"
        assert error.recoverable is True

    def test_non_recoverable(self) -> None:
        """Test non-recoverable error."""
        error: InfrastructureError[None] = InfrastructureError(
            message="Fatal error",
            service="Database",
            recoverable=False,
        )
        
        assert error.recoverable is False

    def test_with_context(self) -> None:
        """Test error with typed context."""
        @dataclass
        class DbContext:
            connection_string: str
            query: str

        ctx = DbContext(connection_string="postgres://...", query="SELECT...")
        error: InfrastructureError[DbContext] = InfrastructureError(
            message="Query failed",
            service="PostgreSQL",
            context=ctx,
        )
        
        assert error.context is not None
        assert error.context.query == "SELECT..."

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        error: InfrastructureError[None] = InfrastructureError(
            message="Failed",
            service="Redis",
            recoverable=False,
        )
        
        result = error.to_dict()
        
        assert result["type"] == "InfrastructureError"
        assert result["service"] == "Redis"
        assert result["recoverable"] is False


class TestMapError:
    """Tests for map_error function."""

    def test_map_domain_error(self) -> None:
        """Test mapping domain error context."""
        original: DomainError[str] = DomainError(
            message="Error",
            error_code="TEST",
            context="original-context",
        )
        
        result = map_error(original, lambda ctx: len(ctx) if ctx else 0)
        
        assert isinstance(result, DomainError)
        assert result.context == 16  # len("original-context")
        assert result.message == "Error"
        assert result.error_code == "TEST"

    def test_map_application_error(self) -> None:
        """Test mapping application error context."""
        original: ApplicationError[dict] = ApplicationError(
            message="Error",
            operation="TestOp",
            context={"key": "value"},
        )
        
        result = map_error(original, lambda ctx: list(ctx.keys()) if ctx else [])
        
        assert isinstance(result, ApplicationError)
        assert result.context == ["key"]
        assert result.operation == "TestOp"

    def test_map_infrastructure_error(self) -> None:
        """Test mapping infrastructure error context."""
        original: InfrastructureError[str] = InfrastructureError(
            message="Error",
            service="Redis",
            context="test",
            recoverable=False,
        )
        
        result = map_error(original, lambda ctx: ctx.upper() if ctx else None)
        
        assert isinstance(result, InfrastructureError)
        assert result.context == "TEST"
        assert result.service == "Redis"
        assert result.recoverable is False

    def test_map_with_none_context(self) -> None:
        """Test mapping error with None context."""
        original: DomainError[None] = DomainError(message="Error")
        
        result = map_error(original, lambda ctx: "mapped" if ctx else None)
        
        assert result.context is None

    def test_preserves_cause(self) -> None:
        """Test that mapping preserves cause."""
        cause = ValueError("Original")
        original: DomainError[str] = DomainError(
            message="Error",
            context="test",
            cause=cause,
        )
        
        result = map_error(original, lambda ctx: ctx)
        
        assert result._cause is cause
