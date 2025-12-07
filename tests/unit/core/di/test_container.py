"""Unit tests for DI Container.

Tests dependency injection, lifetime management, and resolution.
"""

import pytest

from core.di.container import Container
from core.di.lifecycle import Lifetime
from core.di.resolution import CircularDependencyError, ServiceNotRegisteredError


class SimpleService:
    """Simple service for testing."""

    def __init__(self) -> None:
        self.value = "simple"


class DependentService:
    """Service with dependency."""

    def __init__(self, simple: SimpleService) -> None:
        self.simple = simple


class ServiceA:
    """Service A for circular dependency test."""

    def __init__(self, b: "ServiceB") -> None:
        self.b = b


class ServiceB:
    """Service B for circular dependency test."""

    def __init__(self, a: ServiceA) -> None:
        self.a = a


class TestContainerRegistration:
    """Tests for service registration."""

    def test_register_simple_service(self) -> None:
        """Test registering a simple service."""
        container = Container()
        container.register(SimpleService)
        assert container.is_registered(SimpleService)

    def test_register_with_factory(self) -> None:
        """Test registering with custom factory."""
        container = Container()
        container.register(SimpleService, factory=lambda: SimpleService())
        assert container.is_registered(SimpleService)

    def test_register_singleton(self) -> None:
        """Test registering singleton service."""
        container = Container()
        container.register_singleton(SimpleService)
        assert container.is_registered(SimpleService)

    def test_register_scoped(self) -> None:
        """Test registering scoped service."""
        container = Container()
        container.register_scoped(SimpleService)
        assert container.is_registered(SimpleService)

    def test_register_instance(self) -> None:
        """Test registering existing instance."""
        container = Container()
        instance = SimpleService()
        instance.value = "custom"
        container.register_instance(SimpleService, instance)

        resolved = container.resolve(SimpleService)
        assert resolved.value == "custom"
        assert resolved is instance

    def test_is_registered_false(self) -> None:
        """Test is_registered returns False for unregistered."""
        container = Container()
        assert container.is_registered(SimpleService) is False


class TestContainerResolution:
    """Tests for service resolution."""

    def test_resolve_simple_service(self) -> None:
        """Test resolving a simple service."""
        container = Container()
        container.register(SimpleService)

        service = container.resolve(SimpleService)

        assert isinstance(service, SimpleService)
        assert service.value == "simple"

    def test_resolve_with_dependency(self) -> None:
        """Test resolving service with dependency."""
        container = Container()
        container.register(SimpleService)
        container.register(DependentService)

        service = container.resolve(DependentService)

        assert isinstance(service, DependentService)
        assert isinstance(service.simple, SimpleService)

    def test_resolve_unregistered_raises(self) -> None:
        """Test resolving unregistered service raises error."""
        container = Container()

        with pytest.raises(ServiceNotRegisteredError):
            container.resolve(SimpleService)

    def test_resolve_circular_dependency_raises(self) -> None:
        """Test circular dependency detection."""
        container = Container()
        container.register(ServiceA)
        container.register(ServiceB)

        with pytest.raises(CircularDependencyError):
            container.resolve(ServiceA)


class TestLifetimeManagement:
    """Tests for lifetime management."""

    def test_transient_creates_new_instances(self) -> None:
        """Test transient lifetime creates new instances."""
        container = Container()
        container.register(SimpleService, lifetime=Lifetime.TRANSIENT)

        service1 = container.resolve(SimpleService)
        service2 = container.resolve(SimpleService)

        assert service1 is not service2

    def test_singleton_returns_same_instance(self) -> None:
        """Test singleton lifetime returns same instance."""
        container = Container()
        container.register(SimpleService, lifetime=Lifetime.SINGLETON)

        service1 = container.resolve(SimpleService)
        service2 = container.resolve(SimpleService)

        assert service1 is service2

    def test_clear_singletons(self) -> None:
        """Test clearing singleton instances."""
        container = Container()
        container.register(SimpleService, lifetime=Lifetime.SINGLETON)

        service1 = container.resolve(SimpleService)
        container.clear_singletons()
        service2 = container.resolve(SimpleService)

        assert service1 is not service2


class TestContainerScope:
    """Tests for scoped containers."""

    def test_create_scope(self) -> None:
        """Test creating a scope."""
        container = Container()
        container.register_scoped(SimpleService)

        with container.create_scope() as scope:
            assert scope is not None

    def test_scoped_service_same_in_scope(self) -> None:
        """Test scoped service returns same instance within scope."""
        container = Container()
        container.register_scoped(SimpleService)

        with container.create_scope() as scope:
            service1 = scope.resolve(SimpleService)
            service2 = scope.resolve(SimpleService)
            assert service1 is service2

    def test_scoped_service_different_across_scopes(self) -> None:
        """Test scoped service returns different instances across scopes."""
        container = Container()
        container.register_scoped(SimpleService)

        with container.create_scope() as scope1:
            service1 = scope1.resolve(SimpleService)

        with container.create_scope() as scope2:
            service2 = scope2.resolve(SimpleService)

        assert service1 is not service2


class TestContainerStats:
    """Tests for container statistics."""

    def test_get_stats(self) -> None:
        """Test getting container stats."""
        container = Container()
        container.register(SimpleService)
        container.resolve(SimpleService)

        stats = container.get_stats()

        assert stats is not None
        assert stats.total_registrations >= 1
        assert stats.total_resolutions >= 1

    def test_stats_track_singletons(self) -> None:
        """Test stats track singleton creations."""
        container = Container()
        container.register_singleton(SimpleService)
        container.resolve(SimpleService)

        stats = container.get_stats()

        assert stats.singleton_instances_created >= 1


class TestGetRegistration:
    """Tests for get_registration method."""

    def test_get_registration_exists(self) -> None:
        """Test getting existing registration."""
        container = Container()
        container.register(SimpleService, lifetime=Lifetime.SINGLETON)

        registration = container.get_registration(SimpleService)

        assert registration.service_type == SimpleService
        assert registration.lifetime == Lifetime.SINGLETON

    def test_get_registration_not_exists(self) -> None:
        """Test getting non-existent registration raises."""
        container = Container()

        with pytest.raises(ServiceNotRegisteredError):
            container.get_registration(SimpleService)
