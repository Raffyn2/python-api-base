"""Property-based tests for specification algebra.

**Feature: test-coverage-90-percent, Property 3: Specification Algebra**
**Validates: Requirements 5.3**
"""

from dataclasses import dataclass

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.base.patterns.specification import (
    FalseSpecification,
    PredicateSpecification,
    Specification,
    TrueSpecification,
)


@dataclass
class TestItem:
    """Test item for specification testing."""
    
    value: int
    name: str
    active: bool


# Strategies for generating test data
item_strategy = st.builds(
    TestItem,
    value=st.integers(min_value=-1000, max_value=1000),
    name=st.text(min_size=1, max_size=50),
    active=st.booleans()
)


class GreaterThanSpec(Specification[TestItem]):
    """Specification for items with value greater than threshold."""
    
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold
    
    def is_satisfied_by(self, candidate: TestItem) -> bool:
        return candidate.value > self.threshold


class IsActiveSpec(Specification[TestItem]):
    """Specification for active items."""
    
    def is_satisfied_by(self, candidate: TestItem) -> bool:
        return candidate.active


class NameStartsWithSpec(Specification[TestItem]):
    """Specification for items with name starting with prefix."""
    
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
    
    def is_satisfied_by(self, candidate: TestItem) -> bool:
        return candidate.name.startswith(self.prefix)


@pytest.mark.property
class TestSpecificationAlgebraProperties:
    """Property-based tests for specification algebra.
    
    **Feature: test-coverage-90-percent, Property 3: Specification Algebra**
    **Validates: Requirements 5.3**
    """

    @given(item=item_strategy, threshold=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=100)
    def test_and_equals_both_satisfied(
        self, item: TestItem, threshold: int
    ) -> None:
        """AND composition equals both specs being satisfied.
        
        Property: A.and_(B).is_satisfied_by(x) == (A.is_satisfied_by(x) and B.is_satisfied_by(x))
        """
        spec_a = GreaterThanSpec(threshold)
        spec_b = IsActiveSpec()
        
        combined = spec_a & spec_b
        
        expected = spec_a.is_satisfied_by(item) and spec_b.is_satisfied_by(item)
        actual = combined.is_satisfied_by(item)
        
        assert actual == expected

    @given(item=item_strategy, threshold=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=100)
    def test_or_equals_either_satisfied(
        self, item: TestItem, threshold: int
    ) -> None:
        """OR composition equals either spec being satisfied.
        
        Property: A.or_(B).is_satisfied_by(x) == (A.is_satisfied_by(x) or B.is_satisfied_by(x))
        """
        spec_a = GreaterThanSpec(threshold)
        spec_b = IsActiveSpec()
        
        combined = spec_a | spec_b
        
        expected = spec_a.is_satisfied_by(item) or spec_b.is_satisfied_by(item)
        actual = combined.is_satisfied_by(item)
        
        assert actual == expected

    @given(item=item_strategy, threshold=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=100)
    def test_not_equals_negation(self, item: TestItem, threshold: int) -> None:
        """NOT composition equals negation of spec.
        
        Property: A.not_().is_satisfied_by(x) == not A.is_satisfied_by(x)
        """
        spec = GreaterThanSpec(threshold)
        
        negated = ~spec
        
        expected = not spec.is_satisfied_by(item)
        actual = negated.is_satisfied_by(item)
        
        assert actual == expected

    @given(item=item_strategy, threshold=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=100)
    def test_double_negation_identity(self, item: TestItem, threshold: int) -> None:
        """Double negation returns original result.
        
        Property: ~~A.is_satisfied_by(x) == A.is_satisfied_by(x)
        """
        spec = GreaterThanSpec(threshold)
        
        double_negated = ~~spec
        
        expected = spec.is_satisfied_by(item)
        actual = double_negated.is_satisfied_by(item)
        
        assert actual == expected

    @given(item=item_strategy, threshold=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=100)
    def test_de_morgan_and(self, item: TestItem, threshold: int) -> None:
        """De Morgan's law for AND: ~(A & B) == (~A) | (~B).
        
        Property: NOT(A AND B) equals NOT(A) OR NOT(B)
        """
        spec_a = GreaterThanSpec(threshold)
        spec_b = IsActiveSpec()
        
        left = ~(spec_a & spec_b)
        right = (~spec_a) | (~spec_b)
        
        assert left.is_satisfied_by(item) == right.is_satisfied_by(item)

    @given(item=item_strategy, threshold=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=100)
    def test_de_morgan_or(self, item: TestItem, threshold: int) -> None:
        """De Morgan's law for OR: ~(A | B) == (~A) & (~B).
        
        Property: NOT(A OR B) equals NOT(A) AND NOT(B)
        """
        spec_a = GreaterThanSpec(threshold)
        spec_b = IsActiveSpec()
        
        left = ~(spec_a | spec_b)
        right = (~spec_a) & (~spec_b)
        
        assert left.is_satisfied_by(item) == right.is_satisfied_by(item)

    @given(item=item_strategy)
    @settings(max_examples=100)
    def test_and_with_true_identity(self, item: TestItem) -> None:
        """AND with TrueSpecification is identity.
        
        Property: A & True == A
        """
        spec = IsActiveSpec()
        true_spec = TrueSpecification[TestItem]()
        
        combined = spec & true_spec
        
        assert combined.is_satisfied_by(item) == spec.is_satisfied_by(item)

    @given(item=item_strategy)
    @settings(max_examples=100)
    def test_and_with_false_is_false(self, item: TestItem) -> None:
        """AND with FalseSpecification is always False.
        
        Property: A & False == False
        """
        spec = IsActiveSpec()
        false_spec = FalseSpecification[TestItem]()
        
        combined = spec & false_spec
        
        assert combined.is_satisfied_by(item) is False

    @given(item=item_strategy)
    @settings(max_examples=100)
    def test_or_with_true_is_true(self, item: TestItem) -> None:
        """OR with TrueSpecification is always True.
        
        Property: A | True == True
        """
        spec = IsActiveSpec()
        true_spec = TrueSpecification[TestItem]()
        
        combined = spec | true_spec
        
        assert combined.is_satisfied_by(item) is True

    @given(item=item_strategy)
    @settings(max_examples=100)
    def test_or_with_false_identity(self, item: TestItem) -> None:
        """OR with FalseSpecification is identity.
        
        Property: A | False == A
        """
        spec = IsActiveSpec()
        false_spec = FalseSpecification[TestItem]()
        
        combined = spec | false_spec
        
        assert combined.is_satisfied_by(item) == spec.is_satisfied_by(item)

    @given(
        item=item_strategy,
        t1=st.integers(min_value=-500, max_value=500),
        t2=st.integers(min_value=-500, max_value=500)
    )
    @settings(max_examples=100)
    def test_and_commutativity(self, item: TestItem, t1: int, t2: int) -> None:
        """AND is commutative.
        
        Property: A & B == B & A
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = GreaterThanSpec(t2)
        
        left = spec_a & spec_b
        right = spec_b & spec_a
        
        assert left.is_satisfied_by(item) == right.is_satisfied_by(item)

    @given(
        item=item_strategy,
        t1=st.integers(min_value=-500, max_value=500),
        t2=st.integers(min_value=-500, max_value=500)
    )
    @settings(max_examples=100)
    def test_or_commutativity(self, item: TestItem, t1: int, t2: int) -> None:
        """OR is commutative.
        
        Property: A | B == B | A
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = GreaterThanSpec(t2)
        
        left = spec_a | spec_b
        right = spec_b | spec_a
        
        assert left.is_satisfied_by(item) == right.is_satisfied_by(item)

    @given(
        item=item_strategy,
        t1=st.integers(min_value=-300, max_value=300),
        t2=st.integers(min_value=-300, max_value=300),
        t3=st.integers(min_value=-300, max_value=300)
    )
    @settings(max_examples=100)
    def test_and_associativity(
        self, item: TestItem, t1: int, t2: int, t3: int
    ) -> None:
        """AND is associative.
        
        Property: (A & B) & C == A & (B & C)
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = GreaterThanSpec(t2)
        spec_c = GreaterThanSpec(t3)
        
        left = (spec_a & spec_b) & spec_c
        right = spec_a & (spec_b & spec_c)
        
        assert left.is_satisfied_by(item) == right.is_satisfied_by(item)

    @given(
        item=item_strategy,
        t1=st.integers(min_value=-300, max_value=300),
        t2=st.integers(min_value=-300, max_value=300),
        t3=st.integers(min_value=-300, max_value=300)
    )
    @settings(max_examples=100)
    def test_or_associativity(
        self, item: TestItem, t1: int, t2: int, t3: int
    ) -> None:
        """OR is associative.
        
        Property: (A | B) | C == A | (B | C)
        """
        spec_a = GreaterThanSpec(t1)
        spec_b = GreaterThanSpec(t2)
        spec_c = GreaterThanSpec(t3)
        
        left = (spec_a | spec_b) | spec_c
        right = spec_a | (spec_b | spec_c)
        
        assert left.is_satisfied_by(item) == right.is_satisfied_by(item)
