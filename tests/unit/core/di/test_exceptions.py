"""Unit tests for DI exceptions.

Tests DependencyResolutionError, CircularDependencyError,
InvalidFactoryError, ServiceNotRegisteredError.
"""

import pytest

from core.di.resolution import (
    CircularDependencyError,
    DependencyResolutionError,
    InvalidFactoryError,
    ServiceNotRegisteredError,
)


class TestDependencyResolutionError:
    """Tests for DependencyResolutionError."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""

        class MyService:
            pass

        error = DependencyResolutionError(
            service_type=MyService,
            param_name="dependency",
            expected_type=str,
        )
        assert error.service_type is MyService
        assert error.param_name == "dependency"
        assert error.expected_type is str
        assert error.reason is None

    def test_message_format(self) -> None:
        """Test error message format."""

        class UserService:
            pass

        error = DependencyResolutionError(
            service_type=UserService,
            param_name="repository",
            expected_type=dict,
        )
        msg = str(error)
        assert "repository" in msg
        assert "dict" in msg
        assert "UserService" in msg

    def test_with_reason(self) -> None:
        """Test error with reason."""

        class Service:
            pass

        error = DependencyResolutionError(
            service_type=Service,
            param_name="config",
            expected_type=str,
            reason="Not registered",
        )
        assert error.reason == "Not registered"
        assert "Not registered" in str(error)


class TestCircularDependencyError:
    """Tests for CircularDependencyError."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""

        class A:
            pass

        class B:
            pass

        error = CircularDependencyError(chain=[A, B, A])
        assert error.chain == [A, B, A]

    def test_message_format(self) -> None:
        """Test error message shows chain."""

        class ServiceA:
            pass

        class ServiceB:
            pass

        class ServiceC:
            pass

        error = CircularDependencyError(chain=[ServiceA, ServiceB, ServiceC, ServiceA])
        msg = str(error)
        assert "ServiceA" in msg
        assert "ServiceB" in msg
        assert "ServiceC" in msg
        assert "->" in msg

    def test_two_element_chain(self) -> None:
        """Test error with two element chain."""

        class X:
            pass

        class Y:
            pass

        error = CircularDependencyError(chain=[X, Y])
        msg = str(error)
        assert "X -> Y" in msg


class TestInvalidFactoryError:
    """Tests for InvalidFactoryError."""

    def test_with_function(self) -> None:
        """Test error with function factory."""

        def my_factory() -> str:
            return "test"

        error = InvalidFactoryError(
            factory=my_factory,
            reason="Missing type hints",
        )
        assert error.factory is my_factory
        assert error.reason == "Missing type hints"
        assert "my_factory" in str(error)

    def test_with_class(self) -> None:
        """Test error with class factory."""

        class MyClass:
            pass

        error = InvalidFactoryError(
            factory=MyClass,
            reason="Cannot instantiate abstract class",
        )
        assert "MyClass" in str(error)
        assert "Cannot instantiate abstract class" in str(error)

    def test_with_lambda(self) -> None:
        """Test error with lambda factory."""
        factory = lambda: "test"  # noqa: E731
        error = InvalidFactoryError(
            factory=factory,
            reason="Lambda not supported",
        )
        assert "Lambda not supported" in str(error)


class TestServiceNotRegisteredError:
    """Tests for ServiceNotRegisteredError."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""

        class UnknownService:
            pass

        error = ServiceNotRegisteredError(service_type=UnknownService)
        assert error.service_type is UnknownService

    def test_message_format(self) -> None:
        """Test error message format."""

        class MyRepository:
            pass

        error = ServiceNotRegisteredError(service_type=MyRepository)
        msg = str(error)
        assert "MyRepository" in msg
        assert "not registered" in msg.lower()


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_all_inherit_from_exception(self) -> None:
        """Test all DI exceptions inherit from Exception."""

        class Dummy:
            pass

        exceptions = [
            DependencyResolutionError(Dummy, "param", str),
            CircularDependencyError([Dummy]),
            InvalidFactoryError(lambda: None, "reason"),
            ServiceNotRegisteredError(Dummy),
        ]
        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_can_be_caught(self) -> None:
        """Test exceptions can be caught."""

        class Service:
            pass

        with pytest.raises(ServiceNotRegisteredError):
            raise ServiceNotRegisteredError(Service)
