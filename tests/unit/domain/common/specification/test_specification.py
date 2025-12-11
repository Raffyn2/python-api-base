"""Tests for specification pattern module."""

from dataclasses import dataclass

from domain.common.specification.specification import (
    AndSpecification,
    AttributeSpecification,
    ComparisonOperator,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
    Specification,
    contains,
    equals,
    greater_than,
    is_not_null,
    is_null,
    less_than,
    not_equals,
)


@dataclass
class Person:
    """Test entity."""

    name: str
    age: int
    status: str
    email: str | None = None


class IsAdultSpec(Specification[Person]):
    """Test specification for adults."""

    def is_satisfied_by(self, candidate: Person) -> bool:
        return candidate.age >= 18


class IsActiveSpec(Specification[Person]):
    """Test specification for active status."""

    def is_satisfied_by(self, candidate: Person) -> bool:
        return candidate.status == "active"


class TestSpecificationBase:
    """Tests for Specification base class."""

    def test_and_via_operator(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = adult & active
        assert isinstance(combined, AndSpecification)

    def test_or_via_operator(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = adult | active
        assert isinstance(combined, OrSpecification)

    def test_not_via_operator(self) -> None:
        adult = IsAdultSpec()
        negated = ~adult
        assert isinstance(negated, NotSpecification)

    def test_and_operator(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = adult & active
        assert isinstance(combined, AndSpecification)

    def test_or_operator(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = adult | active
        assert isinstance(combined, OrSpecification)

    def test_invert_operator(self) -> None:
        adult = IsAdultSpec()
        negated = ~adult
        assert isinstance(negated, NotSpecification)


class TestAndSpecification:
    """Tests for AndSpecification."""

    def test_both_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = AndSpecification(adult, active)
        person = Person(name="John", age=25, status="active")
        assert combined.is_satisfied_by(person) is True

    def test_left_not_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = AndSpecification(adult, active)
        person = Person(name="John", age=15, status="active")
        assert combined.is_satisfied_by(person) is False

    def test_right_not_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = AndSpecification(adult, active)
        person = Person(name="John", age=25, status="inactive")
        assert combined.is_satisfied_by(person) is False

    def test_neither_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = AndSpecification(adult, active)
        person = Person(name="John", age=15, status="inactive")
        assert combined.is_satisfied_by(person) is False


class TestOrSpecification:
    """Tests for OrSpecification."""

    def test_both_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = OrSpecification(adult, active)
        person = Person(name="John", age=25, status="active")
        assert combined.is_satisfied_by(person) is True

    def test_left_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = OrSpecification(adult, active)
        person = Person(name="John", age=25, status="inactive")
        assert combined.is_satisfied_by(person) is True

    def test_right_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = OrSpecification(adult, active)
        person = Person(name="John", age=15, status="active")
        assert combined.is_satisfied_by(person) is True

    def test_neither_satisfied(self) -> None:
        adult = IsAdultSpec()
        active = IsActiveSpec()
        combined = OrSpecification(adult, active)
        person = Person(name="John", age=15, status="inactive")
        assert combined.is_satisfied_by(person) is False


class TestNotSpecification:
    """Tests for NotSpecification."""

    def test_negates_true(self) -> None:
        adult = IsAdultSpec()
        not_adult = NotSpecification(adult)
        person = Person(name="John", age=25, status="active")
        assert not_adult.is_satisfied_by(person) is False

    def test_negates_false(self) -> None:
        adult = IsAdultSpec()
        not_adult = NotSpecification(adult)
        person = Person(name="John", age=15, status="active")
        assert not_adult.is_satisfied_by(person) is True


class TestPredicateSpecification:
    """Tests for PredicateSpecification."""

    def test_with_lambda(self) -> None:
        spec = PredicateSpecification(lambda p: p.age >= 21)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_with_lambda_false(self) -> None:
        spec = PredicateSpecification(lambda p: p.age >= 21)
        person = Person(name="John", age=18, status="active")
        assert spec.is_satisfied_by(person) is False

    def test_repr(self) -> None:
        spec = PredicateSpecification(lambda p: p.age >= 21)
        assert "PredicateSpecification" in repr(spec)


class TestSpecCombination:
    """Tests for specification combination."""

    def test_creates_predicate_spec(self) -> None:
        s = PredicateSpecification(lambda p: p.age >= 18)
        assert isinstance(s, PredicateSpecification)

    def test_can_combine(self) -> None:
        is_adult = PredicateSpecification(lambda p: p.age >= 18)
        is_active = PredicateSpecification(lambda p: p.status == "active")
        combined = is_adult & is_active
        person = Person(name="John", age=25, status="active")
        assert combined.is_satisfied_by(person) is True


class TestComparisonOperator:
    """Tests for ComparisonOperator enum."""

    def test_eq_value(self) -> None:
        assert ComparisonOperator.EQ.value == "eq"

    def test_ne_value(self) -> None:
        assert ComparisonOperator.NE.value == "ne"

    def test_gt_value(self) -> None:
        assert ComparisonOperator.GT.value == "gt"

    def test_contains_value(self) -> None:
        assert ComparisonOperator.CONTAINS.value == "contains"


class TestAttributeSpecification:
    """Tests for AttributeSpecification."""

    def test_eq_satisfied(self) -> None:
        spec = AttributeSpecification[Person, str]("status", ComparisonOperator.EQ, "active")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_eq_not_satisfied(self) -> None:
        spec = AttributeSpecification[Person, str]("status", ComparisonOperator.EQ, "active")
        person = Person(name="John", age=25, status="inactive")
        assert spec.is_satisfied_by(person) is False

    def test_ne_satisfied(self) -> None:
        spec = AttributeSpecification[Person, str]("status", ComparisonOperator.NE, "deleted")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_gt_satisfied(self) -> None:
        spec = AttributeSpecification[Person, int]("age", ComparisonOperator.GT, 18)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_gt_not_satisfied(self) -> None:
        spec = AttributeSpecification[Person, int]("age", ComparisonOperator.GT, 30)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is False

    def test_ge_satisfied(self) -> None:
        spec = AttributeSpecification[Person, int]("age", ComparisonOperator.GE, 25)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_lt_satisfied(self) -> None:
        spec = AttributeSpecification[Person, int]("age", ComparisonOperator.LT, 30)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_le_satisfied(self) -> None:
        spec = AttributeSpecification[Person, int]("age", ComparisonOperator.LE, 25)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_contains_satisfied(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.CONTAINS, "oh")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_starts_with_satisfied(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.STARTS_WITH, "Jo")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_ends_with_satisfied(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.ENDS_WITH, "hn")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_in_satisfied(self) -> None:
        spec = AttributeSpecification[Person, list]("status", ComparisonOperator.IN, ["active", "pending"])
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_is_null_satisfied(self) -> None:
        spec = AttributeSpecification[Person, None]("email", ComparisonOperator.IS_NULL, None)
        person = Person(name="John", age=25, status="active", email=None)
        assert spec.is_satisfied_by(person) is True

    def test_is_not_null_satisfied(self) -> None:
        spec = AttributeSpecification[Person, None]("email", ComparisonOperator.IS_NOT_NULL, None)
        person = Person(name="John", age=25, status="active", email="john@example.com")
        assert spec.is_satisfied_by(person) is True

    def test_attribute_property(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.EQ, "John")
        assert spec.attribute == "name"

    def test_operator_property(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.EQ, "John")
        assert spec.operator == ComparisonOperator.EQ

    def test_value_property(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.EQ, "John")
        assert spec.value == "John"

    def test_to_expression(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.EQ, "John")
        result = spec.to_expression()
        assert result == ("name", "eq", "John")

    def test_repr(self) -> None:
        spec = AttributeSpecification[Person, str]("name", ComparisonOperator.EQ, "John")
        assert "name" in repr(spec)
        assert "eq" in repr(spec)


class TestFactoryFunctions:
    """Tests for convenience factory functions."""

    def test_equals(self) -> None:
        spec = equals("status", "active")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_not_equals(self) -> None:
        spec = not_equals("status", "deleted")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_greater_than(self) -> None:
        spec = greater_than("age", 18)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_less_than(self) -> None:
        spec = less_than("age", 30)
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_contains(self) -> None:
        spec = contains("name", "oh")
        person = Person(name="John", age=25, status="active")
        assert spec.is_satisfied_by(person) is True

    def test_is_null(self) -> None:
        spec = is_null("email")
        person = Person(name="John", age=25, status="active", email=None)
        assert spec.is_satisfied_by(person) is True

    def test_is_not_null(self) -> None:
        spec = is_not_null("email")
        person = Person(name="John", age=25, status="active", email="john@example.com")
        assert spec.is_satisfied_by(person) is True
