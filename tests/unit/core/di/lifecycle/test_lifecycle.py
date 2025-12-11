"""Tests for dependency lifecycle module.

**Feature: realistic-test-coverage**
**Validates: Requirements 28.1, 28.2, 28.3**
"""

from core.di.lifecycle.lifecycle import Lifetime, Registration


class TestLifetime:
    """Tests for Lifetime enum."""

    def test_transient_value(self) -> None:
        """Test TRANSIENT lifetime value."""
        assert Lifetime.TRANSIENT.value == "transient"

    def test_singleton_value(self) -> None:
        """Test SINGLETON lifetime value."""
        assert Lifetime.SINGLETON.value == "singleton"

    def test_scoped_value(self) -> None:
        """Test SCOPED lifetime value."""
        assert Lifetime.SCOPED.value == "scoped"

    def test_all_lifetimes(self) -> None:
        """Test all lifetime values exist."""
        lifetimes = list(Lifetime)
        assert len(lifetimes) == 3
        assert Lifetime.TRANSIENT in lifetimes
        assert Lifetime.SINGLETON in lifetimes
        assert Lifetime.SCOPED in lifetimes


class TestRegistration:
    """Tests for Registration dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Test creating registration with required fields."""

        class MyService:
            pass

        def factory() -> MyService:
            return MyService()

        reg = Registration(service_type=MyService, factory=factory)
        assert reg.service_type == MyService
        assert reg.factory == factory
        assert reg.lifetime == Lifetime.TRANSIENT
        assert reg.instance is None

    def test_create_with_singleton_lifetime(self) -> None:
        """Test creating registration with singleton lifetime."""

        class MyService:
            pass

        reg = Registration(
            service_type=MyService,
            factory=MyService,
            lifetime=Lifetime.SINGLETON,
        )
        assert reg.lifetime == Lifetime.SINGLETON

    def test_create_with_scoped_lifetime(self) -> None:
        """Test creating registration with scoped lifetime."""

        class MyService:
            pass

        reg = Registration(
            service_type=MyService,
            factory=MyService,
            lifetime=Lifetime.SCOPED,
        )
        assert reg.lifetime == Lifetime.SCOPED

    def test_create_with_instance(self) -> None:
        """Test creating registration with cached instance."""

        class MyService:
            pass

        instance = MyService()
        reg = Registration(
            service_type=MyService,
            factory=MyService,
            instance=instance,
        )
        assert reg.instance is instance

    def test_factory_can_be_called(self) -> None:
        """Test that factory can be called to create instance."""

        class MyService:
            def __init__(self, value: int = 42) -> None:
                self.value = value

        reg = Registration(
            service_type=MyService,
            factory=lambda: MyService(100),
        )
        instance = reg.factory()
        assert isinstance(instance, MyService)
        assert instance.value == 100

    def test_factory_with_class_constructor(self) -> None:
        """Test factory using class constructor directly."""

        class SimpleService:
            pass

        reg = Registration(
            service_type=SimpleService,
            factory=SimpleService,
        )
        instance = reg.factory()
        assert isinstance(instance, SimpleService)

    def test_default_lifetime_is_transient(self) -> None:
        """Test that default lifetime is TRANSIENT."""

        class Service:
            pass

        reg = Registration(service_type=Service, factory=Service)
        assert reg.lifetime == Lifetime.TRANSIENT

    def test_default_instance_is_none(self) -> None:
        """Test that default instance is None."""

        class Service:
            pass

        reg = Registration(service_type=Service, factory=Service)
        assert reg.instance is None

    def test_with_interface_type(self) -> None:
        """Test registration with interface/protocol type."""
        from typing import Protocol

        class IService(Protocol):
            def do_something(self) -> str: ...

        class ConcreteService:
            def do_something(self) -> str:
                return "done"

        reg = Registration(
            service_type=IService,
            factory=ConcreteService,
        )
        assert reg.service_type == IService

    def test_instance_can_be_updated(self) -> None:
        """Test that instance can be updated (for caching)."""

        class Service:
            pass

        reg = Registration(service_type=Service, factory=Service)
        assert reg.instance is None

        # Simulate caching
        cached = Service()
        reg.instance = cached
        assert reg.instance is cached
