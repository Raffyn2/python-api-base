"""Unit tests for interface layer exceptions.

Tests InterfaceError hierarchy and FieldError.
"""

import pytest

from interface.errors.exceptions import (
    BuilderValidationError,
    CompositionError,
    ConfigurationError,
    FieldError,
    InterfaceError,
    InvalidStatusTransitionError,
    NotFoundError,
    RepositoryError,
    ServiceError,
    TransformationError,
    UnwrapError,
    ValidationError,
)


class TestFieldError:
    """Tests for FieldError class."""

    def test_basic_creation(self) -> None:
        error = FieldError(field="email", message="Invalid format", code="invalid")
        assert error.field == "email"
        assert error.message == "Invalid format"
        assert error.code == "invalid"

    def test_repr(self) -> None:
        error = FieldError(field="name", message="Required", code="required")
        repr_str = repr(error)
        assert "name" in repr_str
        assert "Required" in repr_str
        assert "required" in repr_str

    def test_attributes(self) -> None:
        """Test FieldError is a frozen dataclass with expected attributes."""
        error = FieldError(field="age", message="Must be positive", code="min_value")
        # FieldError is a frozen dataclass, no to_dict method
        assert error.field == "age"
        assert error.message == "Must be positive"
        assert error.code == "min_value"


class TestInterfaceError:
    """Tests for InterfaceError base class."""

    def test_basic_creation(self) -> None:
        error = InterfaceError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_is_exception(self) -> None:
        error = InterfaceError("Error")
        assert isinstance(error, Exception)


class TestValidationError:
    """Tests for ValidationError."""

    def test_with_errors(self) -> None:
        errors = [
            FieldError("email", "Invalid", "invalid"),
            FieldError("name", "Required", "required"),
        ]
        error = ValidationError(errors)
        assert len(error.errors) == 2
        assert "2 errors" in str(error)

    def test_empty_errors(self) -> None:
        error = ValidationError([])
        assert len(error.errors) == 0

    def test_inherits_interface_error(self) -> None:
        error = ValidationError([])
        assert isinstance(error, InterfaceError)


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_basic_creation(self) -> None:
        error = NotFoundError("User", "123")
        assert error.resource == "User"
        assert error.id == "123"
        assert "User" in str(error)
        assert "123" in str(error)

    def test_message_format(self) -> None:
        error = NotFoundError("Order", "abc-456")
        assert str(error) == "Order 'abc-456' not found"


class TestUnwrapError:
    """Tests for UnwrapError."""

    def test_basic_creation(self) -> None:
        error = UnwrapError("Cannot unwrap Err")
        assert "Cannot unwrap Err" in str(error)

    def test_inherits_interface_error(self) -> None:
        error = UnwrapError()
        assert isinstance(error, InterfaceError)


class TestBuilderValidationError:
    """Tests for BuilderValidationError."""

    def test_with_missing_fields(self) -> None:
        error = BuilderValidationError(["name", "email"])
        assert error.missing_fields == ["name", "email"]
        assert "name" in str(error)
        assert "email" in str(error)

    def test_empty_fields(self) -> None:
        error = BuilderValidationError([])
        assert error.missing_fields == []


class TestInvalidStatusTransitionError:
    """Tests for InvalidStatusTransitionError."""

    def test_basic_creation(self) -> None:
        error = InvalidStatusTransitionError("pending", "completed")
        assert error.from_status == "pending"
        assert error.to_status == "completed"
        assert "pending" in str(error)
        assert "completed" in str(error)

    def test_message_format(self) -> None:
        error = InvalidStatusTransitionError("draft", "published")
        assert "Cannot transition from draft to published" in str(error)


class TestTransformationError:
    """Tests for TransformationError."""

    def test_basic_creation(self) -> None:
        error = TransformationError("JsonTransformer", "Invalid JSON")
        assert error.transformer == "JsonTransformer"
        assert error.reason == "Invalid JSON"

    def test_message_format(self) -> None:
        error = TransformationError("XmlParser", "Malformed XML")
        assert "XmlParser" in str(error)
        assert "Malformed XML" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_basic_creation(self) -> None:
        error = ConfigurationError("Database", "Missing connection string")
        assert error.component == "Database"
        assert error.issue == "Missing connection string"

    def test_message_format(self) -> None:
        error = ConfigurationError("Cache", "Invalid TTL")
        assert "Cache" in str(error)
        assert "Invalid TTL" in str(error)


class TestCompositionError:
    """Tests for CompositionError."""

    def test_basic_creation(self) -> None:
        error = CompositionError("getUserProfile", "Service unavailable")
        assert error.call_name == "getUserProfile"
        assert error.reason == "Service unavailable"

    def test_message_format(self) -> None:
        error = CompositionError("fetchOrders", "Timeout")
        assert "fetchOrders" in str(error)
        assert "Timeout" in str(error)


class TestRepositoryError:
    """Tests for RepositoryError."""

    def test_basic_creation(self) -> None:
        error = RepositoryError("create", "Duplicate key")
        assert error.operation == "create"
        assert error.reason == "Duplicate key"
        assert error.cause is None

    def test_with_cause(self) -> None:
        cause = ValueError("Original error")
        error = RepositoryError("update", "Failed", cause=cause)
        assert error.cause is cause

    def test_message_format(self) -> None:
        error = RepositoryError("delete", "Foreign key constraint")
        assert "delete" in str(error)
        assert "Foreign key constraint" in str(error)


class TestServiceError:
    """Tests for ServiceError."""

    def test_basic_creation(self) -> None:
        error = ServiceError("processPayment", "Insufficient funds")
        assert error.operation == "processPayment"
        assert error.reason == "Insufficient funds"
        assert error.field_errors == []

    def test_with_field_errors(self) -> None:
        field_errors = [FieldError("amount", "Too low", "min_value")]
        error = ServiceError("transfer", "Validation failed", field_errors)
        assert len(error.field_errors) == 1

    def test_message_format(self) -> None:
        error = ServiceError("sendEmail", "SMTP error")
        assert "sendEmail" in str(error)
        assert "SMTP error" in str(error)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_all_inherit_from_interface_error(self) -> None:
        exceptions = [
            ValidationError([]),
            NotFoundError("Test", "1"),
            UnwrapError(),
            BuilderValidationError([]),
            InvalidStatusTransitionError("a", "b"),
            TransformationError("t", "r"),
            ConfigurationError("c", "i"),
            CompositionError("c", "r"),
            RepositoryError("o", "r"),
            ServiceError("o", "r"),
        ]
        for exc in exceptions:
            assert isinstance(exc, InterfaceError)

    def test_can_catch_with_base_class(self) -> None:
        with pytest.raises(InterfaceError):
            raise NotFoundError("User", "123")
