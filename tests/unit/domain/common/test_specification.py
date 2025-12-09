"""Unit tests for domain/common/specification modules.

**Feature: test-coverage-90-percent**
**Validates: Requirements 2.1**
"""

import pytest

from domain.common.specification.specification import (
    AndSpecification,
    NotSpecification,
    OrSpecification,
    Specification,
)


class IsPositive(Specification[int]):
    """Test specification for positive numbers."""
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > 0


class IsEven(Specification[int]):
    """Test specification for even numbers."""
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate % 2 == 0


class TestDomainSpecification:
    """Tests for domain specification pattern."""

    def test_simple_specification(self) -> None:
        """Simple specification should work."""
        spec = IsPositive()
        
        assert spec.is_satisfied_by(5) is True
        assert spec.is_satisfied_by(-5) is False
        assert spec.is_satisfied_by(0) is False

    def test_and_specification(self) -> None:
        """AND specification should combine correctly."""
        spec = IsPositive() & IsEven()
        
        assert spec.is_satisfied_by(4) is True  # positive and even
        assert spec.is_satisfied_by(3) is False  # positive but odd
        assert spec.is_satisfied_by(-4) is False  # even but negative
        assert spec.is_satisfied_by(-3) is False  # neither

    def test_or_specification(self) -> None:
        """OR specification should combine correctly."""
        spec = IsPositive() | IsEven()
        
        assert spec.is_satisfied_by(4) is True  # both
        assert spec.is_satisfied_by(3) is True  # positive only
        assert spec.is_satisfied_by(-4) is True  # even only
        assert spec.is_satisfied_by(-3) is False  # neither

    def test_not_specification(self) -> None:
        """NOT specification should negate correctly."""
        spec = ~IsPositive()
        
        assert spec.is_satisfied_by(5) is False
        assert spec.is_satisfied_by(-5) is True
        assert spec.is_satisfied_by(0) is True

    def test_complex_composition(self) -> None:
        """Complex specification composition should work."""
        # (positive AND even) OR (NOT positive)
        spec = (IsPositive() & IsEven()) | (~IsPositive())
        
        assert spec.is_satisfied_by(4) is True  # positive and even
        assert spec.is_satisfied_by(3) is False  # positive but odd
        assert spec.is_satisfied_by(-4) is True  # not positive
        assert spec.is_satisfied_by(0) is True  # not positive
