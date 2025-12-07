"""Unit tests for DI lifecycle and registration.

Tests Lifetime enum and Registration dataclass.
"""

import pytest

from core.di.lifecycle import Lifetime, Registration


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

    def test_all_lifetimes_exist(self) -> None:
        """Test all expected lifetimes exist."""
        lifetimes = list(Lifetime)
        assert len(lifetimes) == 3
        assert Lifetime.TRANSIENT in lifetimes
        assert Lifetime.SINGLETON in lifetimes
        assert Lifetime.SCOPED in lifetimes


class TestRegistration:
    """Tests for Registration dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic Registration creation."""

        def factory() -> str:
            return "test"

        reg = Registration(
            service_type=str,
            factory=factory,
        )
        assert reg.service_type is str
        assert reg.factory is factory
        assert reg.lifetime == Lifetime.TRANSIENT
        assert reg.instance is None

    def test_with_lifetime(self) -> None:
        """Test Registration with custom lifetime."""

        def factory() -> int:
            return 42

        reg = Registration(
            service_type=int,
            factory=factory,
            lifetime=Lifetime.SINGLETON,
        )
        assert reg.lifetime == Lifetime.SINGLETON

    def test_with_instance(self) -> None:
        """Test Registration with cached instance."""
        instance = {"key": "value"}

        def factory() -> dict:
            return {}

        reg = Registration(
            service_type=dict,
            factory=factory,
            lifetime=Lifetime.SINGLETON,
            instance=instance,
        )
        assert reg.instance is instance

    def test_generic_type_parameter(self) -> None:
        """Test Registration with generic type."""

        class MyService:
            pass

        def factory() -> MyService:
            return MyService()

        reg = Registration[MyService](
            service_type=MyService,
            factory=factory,
        )
        assert reg.service_type is MyService

