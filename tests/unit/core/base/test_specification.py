"""Unit tests for core/base/patterns/specification.py.

Tests specification pattern creation and composition.

**Feature: test-coverage-90-percent**
**Validates: Requirements 3.1**
"""

from dataclasses import dataclass

from core.base.patterns.specification import (
    AndSpecification,
    AttributeSpecification,
    FalseSpecification,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
    Specification,
    TrueSpecification,
)


@dataclass
class User:
    """Test user class for specifications."""

    name: str
    age: int
    is_active: bool = True
    role: str = "user"


class IsActiveSpec(Specification[User]):
    """Specification for active users."""

    def is_satisfied_by(self, candidate: User) -> bool:
        return candidate.is_active


class IsAdultSpec(Specification[User]):
    """Specification for adult users (age >= 18)."""

    def is_satisfied_by(self, candidate: User) -> bool:
        return candidate.age >= 18


class IsAdminSpec(Specification[User]):
    """Specification for admin users."""

    def is_satisfied_by(self, candidate: User) -> bool:
        return candidate.role == "admin"


class TestSpecification:
    """Tests for base Specification class."""

    def test_simple_specification(self) -> None:
        """Simple specification should evaluate correctly."""
        spec = IsActiveSpec()
        active_user = User(name="John", age=25, is_active=True)
        inactive_user = User(name="Jane", age=30, is_active=False)

        assert spec.is_satisfied_by(active_user) is True
        assert spec.is_satisfied_by(inactive_user) is False


class TestAndSpecification:
    """Tests for AndSpecification class."""

    def test_and_both_true(self) -> None:
        """AND should return True when both specs are satisfied."""
        spec = IsActiveSpec() & IsAdultSpec()
        user = User(name="John", age=25, is_active=True)

        assert spec.is_satisfied_by(user) is True

    def test_and_first_false(self) -> None:
        """AND should return False when first spec is not satisfied."""
        spec = IsActiveSpec() & IsAdultSpec()
        user = User(name="John", age=25, is_active=False)

        assert spec.is_satisfied_by(user) is False

    def test_and_second_false(self) -> None:
        """AND should return False when second spec is not satisfied."""
        spec = IsActiveSpec() & IsAdultSpec()
        user = User(name="John", age=15, is_active=True)

        assert spec.is_satisfied_by(user) is False

    def test_and_both_false(self) -> None:
        """AND should return False when both specs are not satisfied."""
        spec = IsActiveSpec() & IsAdultSpec()
        user = User(name="John", age=15, is_active=False)

        assert spec.is_satisfied_by(user) is False

    def test_and_operator(self) -> None:
        """& operator should create AndSpecification."""
        spec = IsActiveSpec() & IsAdultSpec()

        assert isinstance(spec, AndSpecification)


class TestOrSpecification:
    """Tests for OrSpecification class."""

    def test_or_both_true(self) -> None:
        """OR should return True when both specs are satisfied."""
        spec = IsActiveSpec() | IsAdminSpec()
        user = User(name="John", age=25, is_active=True, role="admin")

        assert spec.is_satisfied_by(user) is True

    def test_or_first_true(self) -> None:
        """OR should return True when first spec is satisfied."""
        spec = IsActiveSpec() | IsAdminSpec()
        user = User(name="John", age=25, is_active=True, role="user")

        assert spec.is_satisfied_by(user) is True

    def test_or_second_true(self) -> None:
        """OR should return True when second spec is satisfied."""
        spec = IsActiveSpec() | IsAdminSpec()
        user = User(name="John", age=25, is_active=False, role="admin")

        assert spec.is_satisfied_by(user) is True

    def test_or_both_false(self) -> None:
        """OR should return False when both specs are not satisfied."""
        spec = IsActiveSpec() | IsAdminSpec()
        user = User(name="John", age=25, is_active=False, role="user")

        assert spec.is_satisfied_by(user) is False

    def test_or_operator(self) -> None:
        """| operator should create OrSpecification."""
        spec = IsActiveSpec() | IsAdminSpec()

        assert isinstance(spec, OrSpecification)


class TestNotSpecification:
    """Tests for NotSpecification class."""

    def test_not_true_becomes_false(self) -> None:
        """NOT should return False when spec is satisfied."""
        spec = ~IsActiveSpec()
        user = User(name="John", age=25, is_active=True)

        assert spec.is_satisfied_by(user) is False

    def test_not_false_becomes_true(self) -> None:
        """NOT should return True when spec is not satisfied."""
        spec = ~IsActiveSpec()
        user = User(name="John", age=25, is_active=False)

        assert spec.is_satisfied_by(user) is True

    def test_not_operator(self) -> None:
        """~ operator should create NotSpecification."""
        spec = ~IsActiveSpec()

        assert isinstance(spec, NotSpecification)


class TestTrueSpecification:
    """Tests for TrueSpecification class."""

    def test_always_returns_true(self) -> None:
        """TrueSpecification should always return True."""
        spec = TrueSpecification[User]()
        user = User(name="John", age=25, is_active=False)

        assert spec.is_satisfied_by(user) is True


class TestFalseSpecification:
    """Tests for FalseSpecification class."""

    def test_always_returns_false(self) -> None:
        """FalseSpecification should always return False."""
        spec = FalseSpecification[User]()
        user = User(name="John", age=25, is_active=True)

        assert spec.is_satisfied_by(user) is False


class TestPredicateSpecification:
    """Tests for PredicateSpecification class."""

    def test_predicate_with_lambda(self) -> None:
        """PredicateSpecification should work with lambda."""
        spec = PredicateSpecification[User](lambda u: u.age > 21)

        assert spec.is_satisfied_by(User(name="John", age=25)) is True
        assert spec.is_satisfied_by(User(name="Jane", age=18)) is False

    def test_predicate_with_function(self) -> None:
        """PredicateSpecification should work with function."""

        def is_senior(user: User) -> bool:
            return user.age >= 65

        spec = PredicateSpecification[User](is_senior)

        assert spec.is_satisfied_by(User(name="John", age=70)) is True
        assert spec.is_satisfied_by(User(name="Jane", age=30)) is False


class TestAttributeSpecification:
    """Tests for AttributeSpecification class."""

    def test_attribute_equals(self) -> None:
        """AttributeSpecification should check attribute equality."""
        spec = AttributeSpecification[User]("role", "admin")

        assert spec.is_satisfied_by(User(name="John", age=25, role="admin")) is True
        assert spec.is_satisfied_by(User(name="Jane", age=25, role="user")) is False

    def test_attribute_not_found(self) -> None:
        """AttributeSpecification should return False for missing attribute."""
        spec = AttributeSpecification[User]("nonexistent", "value")

        assert spec.is_satisfied_by(User(name="John", age=25)) is False


class TestComplexComposition:
    """Tests for complex specification compositions."""

    def test_complex_and_or_not(self) -> None:
        """Complex composition should work correctly."""
        # (active AND adult) OR admin
        spec = (IsActiveSpec() & IsAdultSpec()) | IsAdminSpec()

        # Active adult non-admin
        assert spec.is_satisfied_by(User(name="A", age=25, is_active=True, role="user")) is True
        # Inactive admin
        assert spec.is_satisfied_by(User(name="B", age=25, is_active=False, role="admin")) is True
        # Inactive non-adult non-admin
        assert spec.is_satisfied_by(User(name="C", age=15, is_active=False, role="user")) is False

    def test_double_negation(self) -> None:
        """Double negation should return original result."""
        spec = ~~IsActiveSpec()
        user = User(name="John", age=25, is_active=True)

        assert spec.is_satisfied_by(user) is True

    def test_de_morgan_law_and(self) -> None:
        """De Morgan's law: NOT(A AND B) = NOT(A) OR NOT(B)."""
        user = User(name="John", age=15, is_active=True)  # active but not adult

        spec1 = ~(IsActiveSpec() & IsAdultSpec())
        spec2 = (~IsActiveSpec()) | (~IsAdultSpec())

        assert spec1.is_satisfied_by(user) == spec2.is_satisfied_by(user)

    def test_de_morgan_law_or(self) -> None:
        """De Morgan's law: NOT(A OR B) = NOT(A) AND NOT(B)."""
        user = User(name="John", age=15, is_active=False)  # not active and not adult

        spec1 = ~(IsActiveSpec() | IsAdultSpec())
        spec2 = (~IsActiveSpec()) & (~IsAdultSpec())

        assert spec1.is_satisfied_by(user) == spec2.is_satisfied_by(user)
