"""Unit tests for Specification pattern.

Tests Specification, AndSpecification, OrSpecification, NotSpecification,
TrueSpecification, FalseSpecification, PredicateSpecification, AttributeSpecification.
"""

from dataclasses import dataclass

import pytest

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
class SampleEntity:
    """Sample entity for testing specifications."""

    name: str
    value: int
    is_active: bool = True


class IsActiveSpec(Specification[SampleEntity]):
    """Specification that checks if entity is active."""

    def is_satisfied_by(self, candidate: SampleEntity) -> bool:
        return candidate.is_active


class HasPositiveValueSpec(Specification[SampleEntity]):
    """Specification that checks if entity has positive value."""

    def is_satisfied_by(self, candidate: SampleEntity) -> bool:
        return candidate.value > 0


class HasNameSpec(Specification[SampleEntity]):
    """Specification that checks if entity has specific name."""

    def __init__(self, name: str) -> None:
        self._name = name

    def is_satisfied_by(self, candidate: SampleEntity) -> bool:
        return candidate.name == self._name


class TestSpecification:
    """Tests for base Specification class."""

    def test_is_satisfied_by(self) -> None:
        spec = IsActiveSpec()
        active = SampleEntity(name="test", value=1, is_active=True)
        inactive = SampleEntity(name="test", value=1, is_active=False)

        assert spec.is_satisfied_by(active) is True
        assert spec.is_satisfied_by(inactive) is False

    def test_and_operator(self) -> None:
        spec1 = IsActiveSpec()
        spec2 = HasPositiveValueSpec()
        combined = spec1 & spec2

        assert isinstance(combined, AndSpecification)

    def test_or_operator(self) -> None:
        spec1 = IsActiveSpec()
        spec2 = HasPositiveValueSpec()
        combined = spec1 | spec2

        assert isinstance(combined, OrSpecification)

    def test_not_operator(self) -> None:
        spec = IsActiveSpec()
        negated = ~spec

        assert isinstance(negated, NotSpecification)


class TestAndSpecification:
    """Tests for AndSpecification."""

    def test_both_satisfied(self) -> None:
        spec = IsActiveSpec() & HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=10, is_active=True)

        assert spec.is_satisfied_by(entity) is True

    def test_left_not_satisfied(self) -> None:
        spec = IsActiveSpec() & HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=10, is_active=False)

        assert spec.is_satisfied_by(entity) is False

    def test_right_not_satisfied(self) -> None:
        spec = IsActiveSpec() & HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=-5, is_active=True)

        assert spec.is_satisfied_by(entity) is False

    def test_neither_satisfied(self) -> None:
        spec = IsActiveSpec() & HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=-5, is_active=False)

        assert spec.is_satisfied_by(entity) is False

    def test_chained_and(self) -> None:
        spec = IsActiveSpec() & HasPositiveValueSpec() & HasNameSpec("test")
        entity = SampleEntity(name="test", value=10, is_active=True)

        assert spec.is_satisfied_by(entity) is True

        entity_wrong_name = SampleEntity(name="other", value=10, is_active=True)
        assert spec.is_satisfied_by(entity_wrong_name) is False


class TestOrSpecification:
    """Tests for OrSpecification."""

    def test_both_satisfied(self) -> None:
        spec = IsActiveSpec() | HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=10, is_active=True)

        assert spec.is_satisfied_by(entity) is True

    def test_left_satisfied(self) -> None:
        spec = IsActiveSpec() | HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=-5, is_active=True)

        assert spec.is_satisfied_by(entity) is True

    def test_right_satisfied(self) -> None:
        spec = IsActiveSpec() | HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=10, is_active=False)

        assert spec.is_satisfied_by(entity) is True

    def test_neither_satisfied(self) -> None:
        spec = IsActiveSpec() | HasPositiveValueSpec()
        entity = SampleEntity(name="test", value=-5, is_active=False)

        assert spec.is_satisfied_by(entity) is False

    def test_chained_or(self) -> None:
        spec = IsActiveSpec() | HasPositiveValueSpec() | HasNameSpec("special")
        entity = SampleEntity(name="special", value=-5, is_active=False)

        assert spec.is_satisfied_by(entity) is True


class TestNotSpecification:
    """Tests for NotSpecification."""

    def test_negates_true(self) -> None:
        spec = ~IsActiveSpec()
        entity = SampleEntity(name="test", value=1, is_active=True)

        assert spec.is_satisfied_by(entity) is False

    def test_negates_false(self) -> None:
        spec = ~IsActiveSpec()
        entity = SampleEntity(name="test", value=1, is_active=False)

        assert spec.is_satisfied_by(entity) is True

    def test_double_negation(self) -> None:
        spec = ~~IsActiveSpec()
        entity = SampleEntity(name="test", value=1, is_active=True)

        assert spec.is_satisfied_by(entity) is True


class TestTrueSpecification:
    """Tests for TrueSpecification."""

    def test_always_true(self) -> None:
        spec = TrueSpecification[SampleEntity]()
        entity = SampleEntity(name="test", value=1)

        assert spec.is_satisfied_by(entity) is True

    def test_with_any_entity(self) -> None:
        spec = TrueSpecification[SampleEntity]()
        entity = SampleEntity(name="", value=-100, is_active=False)

        assert spec.is_satisfied_by(entity) is True


class TestFalseSpecification:
    """Tests for FalseSpecification."""

    def test_always_false(self) -> None:
        spec = FalseSpecification[SampleEntity]()
        entity = SampleEntity(name="test", value=1)

        assert spec.is_satisfied_by(entity) is False

    def test_with_any_entity(self) -> None:
        spec = FalseSpecification[SampleEntity]()
        entity = SampleEntity(name="perfect", value=100, is_active=True)

        assert spec.is_satisfied_by(entity) is False


class TestPredicateSpecification:
    """Tests for PredicateSpecification."""

    def test_with_lambda(self) -> None:
        spec = PredicateSpecification[SampleEntity](lambda e: e.value > 50)
        high_value = SampleEntity(name="test", value=100)
        low_value = SampleEntity(name="test", value=10)

        assert spec.is_satisfied_by(high_value) is True
        assert spec.is_satisfied_by(low_value) is False

    def test_with_function(self) -> None:
        def is_premium(entity: SampleEntity) -> bool:
            return entity.is_active and entity.value >= 100

        spec = PredicateSpecification[SampleEntity](is_premium)
        premium = SampleEntity(name="test", value=100, is_active=True)
        not_premium = SampleEntity(name="test", value=50, is_active=True)

        assert spec.is_satisfied_by(premium) is True
        assert spec.is_satisfied_by(not_premium) is False

    def test_combined_with_other_specs(self) -> None:
        predicate_spec = PredicateSpecification[SampleEntity](lambda e: len(e.name) > 3)
        combined = predicate_spec & IsActiveSpec()

        long_name_active = SampleEntity(name="longname", value=1, is_active=True)
        short_name_active = SampleEntity(name="ab", value=1, is_active=True)

        assert combined.is_satisfied_by(long_name_active) is True
        assert combined.is_satisfied_by(short_name_active) is False


class TestAttributeSpecification:
    """Tests for AttributeSpecification."""

    def test_attribute_equals(self) -> None:
        spec = AttributeSpecification[SampleEntity]("name", "test")
        matching = SampleEntity(name="test", value=1)
        not_matching = SampleEntity(name="other", value=1)

        assert spec.is_satisfied_by(matching) is True
        assert spec.is_satisfied_by(not_matching) is False

    def test_boolean_attribute(self) -> None:
        spec = AttributeSpecification[SampleEntity]("is_active", True)
        active = SampleEntity(name="test", value=1, is_active=True)
        inactive = SampleEntity(name="test", value=1, is_active=False)

        assert spec.is_satisfied_by(active) is True
        assert spec.is_satisfied_by(inactive) is False

    def test_numeric_attribute(self) -> None:
        spec = AttributeSpecification[SampleEntity]("value", 42)
        matching = SampleEntity(name="test", value=42)
        not_matching = SampleEntity(name="test", value=100)

        assert spec.is_satisfied_by(matching) is True
        assert spec.is_satisfied_by(not_matching) is False

    def test_nonexistent_attribute(self) -> None:
        spec = AttributeSpecification[SampleEntity]("nonexistent", "value")
        entity = SampleEntity(name="test", value=1)

        assert spec.is_satisfied_by(entity) is False


class TestComplexSpecificationComposition:
    """Tests for complex specification compositions."""

    def test_complex_and_or_not(self) -> None:
        # (active AND positive) OR (NOT active AND name="special")
        spec = (IsActiveSpec() & HasPositiveValueSpec()) | (
            ~IsActiveSpec() & HasNameSpec("special")
        )

        active_positive = SampleEntity(name="test", value=10, is_active=True)
        inactive_special = SampleEntity(name="special", value=-5, is_active=False)
        inactive_normal = SampleEntity(name="normal", value=-5, is_active=False)

        assert spec.is_satisfied_by(active_positive) is True
        assert spec.is_satisfied_by(inactive_special) is True
        assert spec.is_satisfied_by(inactive_normal) is False

    def test_filter_list_with_specification(self) -> None:
        entities = [
            SampleEntity(name="a", value=10, is_active=True),
            SampleEntity(name="b", value=-5, is_active=True),
            SampleEntity(name="c", value=20, is_active=False),
            SampleEntity(name="d", value=30, is_active=True),
        ]

        spec = IsActiveSpec() & HasPositiveValueSpec()
        filtered = [e for e in entities if spec.is_satisfied_by(e)]

        assert len(filtered) == 2
        assert filtered[0].name == "a"
        assert filtered[1].name == "d"

