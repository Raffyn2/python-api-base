"""Property-based tests for Specification pattern.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 11.1-11.5**

Property tests for:
- Property 5: Specification Composition Laws (Boolean algebra)
- Property 6: Specification AND/OR/NOT consistency
"""

from dataclasses import dataclass
from decimal import Decimal

from hypothesis import given, settings, strategies as st

from core.base.patterns.specification import (
    AttributeSpecification,
    FalseSpecification,
    PredicateSpecification,
    Specification,
    TrueSpecification,
)
from domain.examples.item.entity import ItemExample, ItemExampleStatus, Money
from domain.examples.item.specifications import (
    ItemExampleActiveSpec,
    ItemExampleInStockSpec,
    ItemExamplePriceRangeSpec,
)

# === Test Fixtures ===


@dataclass
class SampleEntity:
    """Simple sample entity for specification tests."""

    value: int
    name: str = "test"
    active: bool = True


class GreaterThanSpec(Specification[SampleEntity]):
    """Specification: entity.value > threshold."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, candidate: SampleEntity) -> bool:
        return candidate.value > self.threshold


class LessThanSpec(Specification[SampleEntity]):
    """Specification: entity.value < threshold."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, candidate: SampleEntity) -> bool:
        return candidate.value < self.threshold


class IsActiveSpec(Specification[SampleEntity]):
    """Specification: entity.active is True."""

    def is_satisfied_by(self, candidate: SampleEntity) -> bool:
        return candidate.active


# === Strategies ===


entity_strategy = st.builds(
    SampleEntity,
    value=st.integers(min_value=-1000, max_value=1000),
    name=st.text(min_size=1, max_size=20),
    active=st.booleans(),
)

threshold_strategy = st.integers(min_value=-500, max_value=500)


# === Property Tests ===


class TestSpecificationCompositionLaws:
    """Property 5: Specification Composition Laws.

    Specifications SHALL obey boolean algebra laws:
    - Identity: A & True = A, A | False = A
    - Annihilation: A & False = False, A | True = True
    - Idempotence: A & A = A, A | A = A
    - Complement: A & ~A = False, A | ~A = True
    - De Morgan: ~(A & B) = ~A | ~B, ~(A | B) = ~A & ~B

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_identity_law_and(self, entity: SampleEntity, threshold: int) -> None:
        """A & True = A (Identity law for AND).

        **Feature: api-best-practices-review-2025, Property 5: Specification Composition**
        **Validates: Requirements 5.1**
        """
        spec_a = GreaterThanSpec(threshold)
        spec_true = TrueSpecification[SampleEntity]()

        combined = spec_a & spec_true

        assert combined.is_satisfied_by(entity) == spec_a.is_satisfied_by(entity)

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_identity_law_or(self, entity: SampleEntity, threshold: int) -> None:
        """A | False = A (Identity law for OR).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.1**
        """
        spec_a = GreaterThanSpec(threshold)
        spec_false = FalseSpecification[SampleEntity]()

        combined = spec_a | spec_false

        assert combined.is_satisfied_by(entity) == spec_a.is_satisfied_by(entity)

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_annihilation_law_and(self, entity: SampleEntity, threshold: int) -> None:
        """A & False = False (Annihilation law for AND).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.2**
        """
        spec_a = GreaterThanSpec(threshold)
        spec_false = FalseSpecification[SampleEntity]()

        combined = spec_a & spec_false

        assert combined.is_satisfied_by(entity) is False

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_annihilation_law_or(self, entity: SampleEntity, threshold: int) -> None:
        """A | True = True (Annihilation law for OR).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.2**
        """
        spec_a = GreaterThanSpec(threshold)
        spec_true = TrueSpecification[SampleEntity]()

        combined = spec_a | spec_true

        assert combined.is_satisfied_by(entity) is True

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_idempotence_law_and(self, entity: SampleEntity, threshold: int) -> None:
        """A & A = A (Idempotence law for AND).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.3**
        """
        spec_a = GreaterThanSpec(threshold)

        combined = spec_a & spec_a

        assert combined.is_satisfied_by(entity) == spec_a.is_satisfied_by(entity)

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_idempotence_law_or(self, entity: SampleEntity, threshold: int) -> None:
        """A | A = A (Idempotence law for OR).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.3**
        """
        spec_a = GreaterThanSpec(threshold)

        combined = spec_a | spec_a

        assert combined.is_satisfied_by(entity) == spec_a.is_satisfied_by(entity)

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_complement_law_and(self, entity: SampleEntity, threshold: int) -> None:
        """A & ~A = False (Complement law for AND).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.4**
        """
        spec_a = GreaterThanSpec(threshold)

        combined = spec_a & ~spec_a

        assert combined.is_satisfied_by(entity) is False

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_complement_law_or(self, entity: SampleEntity, threshold: int) -> None:
        """A | ~A = True (Complement law for OR).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.4**
        """
        spec_a = GreaterThanSpec(threshold)

        combined = spec_a | ~spec_a

        assert combined.is_satisfied_by(entity) is True

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, t1=threshold_strategy, t2=threshold_strategy)
    def test_de_morgan_law_and(self, entity: SampleEntity, t1: int, t2: int) -> None:
        """~(A & B) = ~A | ~B (De Morgan's law for AND).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.5**
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = LessThanSpec(t2)

        left = ~(spec_a & spec_b)
        right = (~spec_a) | (~spec_b)

        assert left.is_satisfied_by(entity) == right.is_satisfied_by(entity)

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, t1=threshold_strategy, t2=threshold_strategy)
    def test_de_morgan_law_or(self, entity: SampleEntity, t1: int, t2: int) -> None:
        """~(A | B) = ~A & ~B (De Morgan's law for OR).

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 5.5**
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = LessThanSpec(t2)

        left = ~(spec_a | spec_b)
        right = (~spec_a) & (~spec_b)

        assert left.is_satisfied_by(entity) == right.is_satisfied_by(entity)


class TestSpecificationComposition:
    """Property 6: Specification AND/OR/NOT consistency.

    For any two specifications A and B and any candidate c:
    - (A & B).is_satisfied_by(c) == A.is_satisfied_by(c) and B.is_satisfied_by(c)
    - (A | B).is_satisfied_by(c) == A.is_satisfied_by(c) or B.is_satisfied_by(c)
    - (~A).is_satisfied_by(c) == not A.is_satisfied_by(c)

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 11.1, 11.2, 11.3**
    """

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, t1=threshold_strategy, t2=threshold_strategy)
    def test_and_composition_consistency(
        self, entity: SampleEntity, t1: int, t2: int
    ) -> None:
        """AND composition SHALL match manual AND.

        **Feature: api-best-practices-review-2025, Property 6**
        **Validates: Requirements 11.1**
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = LessThanSpec(t2)

        composed = spec_a & spec_b
        manual = spec_a.is_satisfied_by(entity) and spec_b.is_satisfied_by(entity)

        assert composed.is_satisfied_by(entity) == manual

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, t1=threshold_strategy, t2=threshold_strategy)
    def test_or_composition_consistency(
        self, entity: SampleEntity, t1: int, t2: int
    ) -> None:
        """OR composition SHALL match manual OR.

        **Feature: api-best-practices-review-2025, Property 6**
        **Validates: Requirements 11.2**
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = LessThanSpec(t2)

        composed = spec_a | spec_b
        manual = spec_a.is_satisfied_by(entity) or spec_b.is_satisfied_by(entity)

        assert composed.is_satisfied_by(entity) == manual

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_not_composition_consistency(
        self, entity: SampleEntity, threshold: int
    ) -> None:
        """NOT composition SHALL match manual NOT.

        **Feature: api-best-practices-review-2025, Property 6**
        **Validates: Requirements 11.3**
        """
        spec_a = GreaterThanSpec(threshold)

        composed = ~spec_a
        manual = not spec_a.is_satisfied_by(entity)

        assert composed.is_satisfied_by(entity) == manual


class TestPredicateSpecification:
    """Tests for PredicateSpecification.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 11.4**
    """

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy, threshold=threshold_strategy)
    def test_predicate_spec_matches_lambda(
        self, entity: SampleEntity, threshold: int
    ) -> None:
        """PredicateSpecification SHALL match lambda behavior.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 11.4**
        """
        predicate = lambda e: e.value > threshold
        spec = PredicateSpecification[SampleEntity](predicate)

        assert spec.is_satisfied_by(entity) == predicate(entity)


class TestAttributeSpecification:
    """Tests for AttributeSpecification.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 11.5**
    """

    @settings(max_examples=50, deadline=None)
    @given(entity=entity_strategy)
    def test_attribute_spec_matches_attribute(self, entity: SampleEntity) -> None:
        """AttributeSpecification SHALL match attribute value.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 11.5**
        """
        spec = AttributeSpecification[SampleEntity]("active", True)

        assert spec.is_satisfied_by(entity) == (entity.active is True)


class TestItemExampleSpecifications:
    """Tests for domain-specific ItemExample specifications.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 11.1-11.5**
    """

    def _create_item(
        self,
        name: str = "Test",
        price: Decimal = Decimal("10.00"),
        quantity: int = 1,
        status: ItemExampleStatus = ItemExampleStatus.ACTIVE,
    ) -> ItemExample:
        """Create a test item without domain events."""
        return ItemExample(
            id="test-id",
            name=name,
            description="Test item",
            sku="TST-001",
            price=Money(price),
            quantity=quantity,
            status=status,
        )

    def test_active_spec_filters_active_items(self) -> None:
        """ItemExampleActiveSpec SHALL filter active items.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 11.1**
        """
        active_item = self._create_item(status=ItemExampleStatus.ACTIVE)
        inactive_item = self._create_item(status=ItemExampleStatus.INACTIVE)

        spec = ItemExampleActiveSpec()

        assert spec.is_satisfied_by(active_item) is True
        assert spec.is_satisfied_by(inactive_item) is False

    def test_in_stock_spec_filters_by_quantity(self) -> None:
        """ItemExampleInStockSpec SHALL filter by quantity.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 11.2**
        """
        in_stock = self._create_item(quantity=10)
        out_of_stock = self._create_item(quantity=0)

        spec = ItemExampleInStockSpec()

        assert spec.is_satisfied_by(in_stock) is True
        assert spec.is_satisfied_by(out_of_stock) is False

    def test_price_range_spec_filters_by_price(self) -> None:
        """ItemExamplePriceRangeSpec SHALL filter by price range.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 11.3**
        """
        cheap = self._create_item(price=Decimal("10.00"))
        expensive = self._create_item(price=Decimal("1000.00"))

        spec = ItemExamplePriceRangeSpec(
            min_price=Decimal("5.00"),
            max_price=Decimal("50.00"),
        )

        assert spec.is_satisfied_by(cheap) is True
        assert spec.is_satisfied_by(expensive) is False

    def test_composed_item_specifications(self) -> None:
        """Composed ItemExample specs SHALL work correctly.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 11.4**
        """
        item = self._create_item(
            price=Decimal("25.00"),
            quantity=5,
            status=ItemExampleStatus.ACTIVE,
        )

        # Active AND in stock AND in price range
        spec = (
            ItemExampleActiveSpec()
            & ItemExampleInStockSpec()
            & ItemExamplePriceRangeSpec(Decimal("10.00"), Decimal("50.00"))
        )

        assert spec.is_satisfied_by(item) is True

        # Inactive item - should fail spec
        inactive_item = self._create_item(
            price=Decimal("25.00"),
            quantity=5,
            status=ItemExampleStatus.INACTIVE,
        )
        assert spec.is_satisfied_by(inactive_item) is False
