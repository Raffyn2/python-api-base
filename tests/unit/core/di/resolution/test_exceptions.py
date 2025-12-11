"""Tests for DI resolution exceptions.

**Feature: realistic-test-coverage**
**Validates: Requirements 4.1, 4.2, 4.4, 4.5**
"""

import pytest

from core.di.resolution.exceptions import (
    CircularDependencyError,
    DependencyResolutionError,
    InvalidFactoryError,
    ServiceNotRegisteredError,
)


class TestDependencyResolutionError:
    """Tests for DependencyResolutionError."""

    def test_create_with_required_params(self) -> None:
        """Test creating error with required parameters."""

        class MyService:
            pass

        class DependencyType:
            pass

        error = DependencyResolutionError(
            service_type=MyService,
            param_name="dependency",
            expected_type=DependencyType,
        )
        assert error.service_type == MyService
        assert error.param_name == "dependency"
        assert error.expected_type == DependencyType
        assert error.reason is None

    def test_create_with_reason(self) -> None:
        """Test creating error with reason."""

        class Service:
            pass

        class Dep:
            pass

        error = DependencyResolutionError(
            service_type=Service,
            param_name="dep",
            expected_type=Dep,
            reason="Not registered",
        )
        assert error.reason == "Not registered"
        assert "Not registered" in str(error)

    def test_message_format(self) -> None:
        """Test error message format."""

        class UserService:
            pass

        class Repository:
            pass

        error = DependencyResolutionError(
            service_type=UserService,
            param_name="repo",
            expected_type=Repository,
        )
        msg = str(error)
        assert "repo" in msg
        assert "Repository" in msg
        assert "UserService" in msg

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""

        class S:
            pass

        class T:
            pass

        error = DependencyResolutionError(S, "p", T)
        assert isinstance(error, Exception)


class TestCircularDependencyError:
    """Tests for CircularDependencyError."""

    def test_create_with_chain(self) -> None:
        """Test creating error with dependency chain."""

        class A:
            pass

        class B:
            pass

        class C:
            pass

        chain = [A, B, C, A]
        error = CircularDependencyError(chain)
        assert error.chain == chain

    def test_message_format(self) -> None:
        """Test error message format."""

        class ServiceA:
            pass

        class ServiceB:
            pass

        chain = [ServiceA, ServiceB, ServiceA]
        error = CircularDependencyError(chain)
        msg = str(error)
        assert "Circular dependency detected" in msg
        assert "ServiceA" in msg
        assert "ServiceB" in msg
        assert "->" in msg

    def test_single_type_chain(self) -> None:
        """Test with single type in chain."""

        class SelfRef:
            pass

        chain = [SelfRef, SelfRef]
        error = CircularDependencyError(chain)
        assert "SelfRef -> SelfRef" in str(error)

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""

        class X:
            pass

        error = CircularDependencyError([X])
        assert isinstance(error, Exception)


class TestInvalidFactoryError:
    """Tests for InvalidFactoryError."""

    def test_create_with_function(self) -> None:
        """Test creating error with function factory."""

        def my_factory() -> str:
            return "test"

        error = InvalidFactoryError(my_factory, "Missing return type")
        assert error.factory == my_factory
        assert error.reason == "Missing return type"

    def test_create_with_class(self) -> None:
        """Test creating error with class factory."""

        class MyClass:
            pass

        error = InvalidFactoryError(MyClass, "Invalid constructor")
        assert error.factory == MyClass
        assert "MyClass" in str(error)

    def test_message_format(self) -> None:
        """Test error message format."""

        def create_service() -> None:
            pass

        error = InvalidFactoryError(create_service, "No parameters allowed")
        msg = str(error)
        assert "Invalid factory" in msg
        assert "create_service" in msg
        assert "No parameters allowed" in msg

    def test_with_lambda(self) -> None:
        """Test with lambda factory."""

        def factory():
            return "test"

        error = InvalidFactoryError(factory, "Lambda not supported")
        assert error.factory == factory
        assert "Lambda not supported" in str(error)

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""

        def f() -> None:
            pass

        error = InvalidFactoryError(f, "reason")
        assert isinstance(error, Exception)


class TestServiceNotRegisteredError:
    """Tests for ServiceNotRegisteredError."""

    def test_create_with_service_type(self) -> None:
        """Test creating error with service type."""

        class MyService:
            pass

        error = ServiceNotRegisteredError(MyService)
        assert error.service_type == MyService

    def test_message_format(self) -> None:
        """Test error message format."""

        class UserRepository:
            pass

        error = ServiceNotRegisteredError(UserRepository)
        msg = str(error)
        assert "UserRepository" in msg
        assert "not registered" in msg

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""

        class S:
            pass

        error = ServiceNotRegisteredError(S)
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test that error can be raised and caught."""

        class TestService:
            pass

        with pytest.raises(ServiceNotRegisteredError) as exc_info:
            raise ServiceNotRegisteredError(TestService)
        assert exc_info.value.service_type == TestService
