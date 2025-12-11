"""Unit tests for domain layer.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 3.1, 3.2, 3.3**
"""

from typing import Any

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import BaseModel

from domain.common import (
    Specification,
)


# Test Value Objects using Pydantic BaseModel
class EmailAddress(BaseModel):
    """Test value object for email addresses."""

    value: str

    def __init__(self, value: str, **kwargs: Any) -> None:
        if "@" not in value:
            raise ValueError("Invalid email address")
        super().__init__(value=value, **kwargs)

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EmailAddress):
            return False
        return self.value == other.value


class TestMoney(BaseModel):
    """Test value object for money."""

    amount: int
    currency: str = "USD"

    def __init__(self, amount: int, currency: str = "USD", **kwargs: Any) -> None:
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        super().__init__(amount=amount, currency=currency, **kwargs)

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TestMoney):
            return False
        return self.amount == other.amount and self.currency == other.currency


# Test Specifications
class IsActiveSpecification(Specification):
    """Specification for active entities."""

    def is_satisfied_by(self, candidate: Any) -> bool:
        return getattr(candidate, "is_active", False)


class HasMinimumBalanceSpecification(Specification):
    """Specification for minimum balance."""

    def __init__(self, minimum: int) -> None:
        self.minimum = minimum

    def is_satisfied_by(self, candidate: Any) -> bool:
        return getattr(candidate, "balance", 0) >= self.minimum


class TestValueObject:
    """Tests for ValueObject base class."""

    def test_value_object_creation(self) -> None:
        """Test value object creation with valid data."""
        email = EmailAddress(value="test@example.com")
        assert email.value == "test@example.com"

    def test_value_object_validation(self) -> None:
        """Test value object validation rejects invalid data."""
        with pytest.raises(ValueError):
            EmailAddress(value="invalid-email")

    def test_value_object_equality(self) -> None:
        """Test value objects with same values are equal."""
        email1 = EmailAddress(value="test@example.com")
        email2 = EmailAddress(value="test@example.com")
        assert email1 == email2

    def test_value_object_inequality(self) -> None:
        """Test value objects with different values are not equal."""
        email1 = EmailAddress(value="test1@example.com")
        email2 = EmailAddress(value="test2@example.com")
        assert email1 != email2

    def test_value_object_hash_equality(self) -> None:
        """Test equal value objects have same hash."""
        email1 = EmailAddress(value="test@example.com")
        email2 = EmailAddress(value="test@example.com")
        assert hash(email1) == hash(email2)

    def test_money_value_object(self) -> None:
        """Test Money value object."""
        money = TestMoney(amount=100, currency="USD")
        assert money.amount == 100
        assert money.currency == "USD"

    def test_money_negative_amount_rejected(self) -> None:
        """Test Money rejects negative amounts."""
        with pytest.raises(ValueError):
            TestMoney(amount=-100)


class TestSpecification:
    """Tests for Specification pattern."""

    @pytest.fixture()
    def active_entity(self) -> Any:
        """Create active entity."""
        entity = type("Entity", (), {"is_active": True, "balance": 100})()
        return entity

    @pytest.fixture()
    def inactive_entity(self) -> Any:
        """Create inactive entity."""
        entity = type("Entity", (), {"is_active": False, "balance": 50})()
        return entity

    def test_is_satisfied_by(self, active_entity: Any) -> None:
        """Test basic specification satisfaction."""
        spec = IsActiveSpecification()
        assert spec.is_satisfied_by(active_entity) is True

    def test_is_not_satisfied_by(self, inactive_entity: Any) -> None:
        """Test specification not satisfied."""
        spec = IsActiveSpecification()
        assert spec.is_satisfied_by(inactive_entity) is False

    def test_and_specification_both_true(self, active_entity: Any) -> None:
        """Test AND specification when both are satisfied."""
        spec1 = IsActiveSpecification()
        spec2 = HasMinimumBalanceSpecification(minimum=50)
        and_spec = spec1 & spec2

        assert and_spec.is_satisfied_by(active_entity) is True

    def test_and_specification_one_false(self, active_entity: Any) -> None:
        """Test AND specification when one is not satisfied."""
        spec1 = IsActiveSpecification()
        spec2 = HasMinimumBalanceSpecification(minimum=200)
        and_spec = spec1 & spec2

        assert and_spec.is_satisfied_by(active_entity) is False

    def test_or_specification_one_true(self, inactive_entity: Any) -> None:
        """Test OR specification when one is satisfied."""
        spec1 = IsActiveSpecification()
        spec2 = HasMinimumBalanceSpecification(minimum=50)
        or_spec = spec1 | spec2

        assert or_spec.is_satisfied_by(inactive_entity) is True

    def test_or_specification_both_false(self, inactive_entity: Any) -> None:
        """Test OR specification when neither is satisfied."""
        spec1 = IsActiveSpecification()
        spec2 = HasMinimumBalanceSpecification(minimum=100)
        or_spec = spec1 | spec2

        assert or_spec.is_satisfied_by(inactive_entity) is False

    def test_not_specification(self, inactive_entity: Any) -> None:
        """Test NOT specification."""
        spec = IsActiveSpecification()
        not_spec = ~spec

        assert not_spec.is_satisfied_by(inactive_entity) is True


class TestValueObjectProperties:
    """Property-based tests for ValueObject.

    **Feature: test-coverage-80-percent-v3, Property 6: Value Object Equality**
    **Validates: Requirements 3.2**
    """

    @given(
        amount1=st.integers(min_value=0, max_value=1000000),
        amount2=st.integers(min_value=0, max_value=1000000),
        currency=st.sampled_from(["USD", "EUR", "GBP"]),
    )
    @settings(max_examples=100, deadline=5000)
    def test_equality_reflexive(self, amount1: int, amount2: int, currency: str) -> None:
        """Property: Value objects with same values are equal.

        **Feature: test-coverage-80-percent-v3, Property 6: Value Object Equality**
        **Validates: Requirements 3.2**
        """
        money1 = TestMoney(amount=amount1, currency=currency)
        money2 = TestMoney(amount=amount1, currency=currency)

        # Same values should be equal
        assert money1 == money2
        assert hash(money1) == hash(money2)

        # Different values should not be equal (unless amounts happen to match)
        money3 = TestMoney(amount=amount2, currency=currency)
        if amount1 == amount2:
            assert money1 == money3
        else:
            assert money1 != money3


class TestSpecificationProperties:
    """Property-based tests for Specification composition.

    **Feature: test-coverage-80-percent-v3, Property 7: Specification Composition**
    **Validates: Requirements 3.3**
    """

    @given(
        is_active=st.booleans(),
        balance=st.integers(min_value=0, max_value=1000),
        min_balance=st.integers(min_value=0, max_value=500),
    )
    @settings(max_examples=100, deadline=5000)
    def test_and_composition(self, is_active: bool, balance: int, min_balance: int) -> None:
        """Property: AND composition is satisfied only when both specs are satisfied.

        **Feature: test-coverage-80-percent-v3, Property 7: Specification Composition**
        **Validates: Requirements 3.3**
        """
        entity = type("Entity", (), {"is_active": is_active, "balance": balance})()

        spec1 = IsActiveSpecification()
        spec2 = HasMinimumBalanceSpecification(minimum=min_balance)
        and_spec = spec1 & spec2

        expected = is_active and (balance >= min_balance)
        assert and_spec.is_satisfied_by(entity) == expected

    @given(
        is_active=st.booleans(),
        balance=st.integers(min_value=0, max_value=1000),
        min_balance=st.integers(min_value=0, max_value=500),
    )
    @settings(max_examples=100, deadline=5000)
    def test_or_composition(self, is_active: bool, balance: int, min_balance: int) -> None:
        """Property: OR composition is satisfied when at least one spec is satisfied.

        **Feature: test-coverage-80-percent-v3, Property 7: Specification Composition**
        **Validates: Requirements 3.3**
        """
        entity = type("Entity", (), {"is_active": is_active, "balance": balance})()

        spec1 = IsActiveSpecification()
        spec2 = HasMinimumBalanceSpecification(minimum=min_balance)
        or_spec = spec1 | spec2

        expected = is_active or (balance >= min_balance)
        assert or_spec.is_satisfied_by(entity) == expected

    @given(is_active=st.booleans())
    @settings(max_examples=100, deadline=5000)
    def test_not_composition(self, is_active: bool) -> None:
        """Property: NOT composition inverts the specification result.

        **Feature: test-coverage-80-percent-v3, Property 7: Specification Composition**
        **Validates: Requirements 3.3**
        """
        entity = type("Entity", (), {"is_active": is_active})()

        spec = IsActiveSpecification()
        not_spec = ~spec

        assert not_spec.is_satisfied_by(entity) == (not is_active)


from decimal import Decimal

from domain.examples.item.entity import (
    ItemExample,
    ItemExampleCreated,
    ItemExampleDeleted,
    ItemExampleStatus,
    ItemExampleUpdated,
    Money as ItemMoney,
)


class TestItemExampleMoney:
    """Tests for ItemExample Money value object."""

    def test_money_creation(self) -> None:
        """Test Money creation with valid data."""
        money = ItemMoney(Decimal("99.90"), "BRL")
        assert money.amount == Decimal("99.90")
        assert money.currency == "BRL"

    def test_money_negative_amount_allowed(self) -> None:
        """Test Money allows negative amounts (for refunds, etc)."""
        money = ItemMoney(Decimal("-10.00"))
        assert money.amount == Decimal("-10.00")

    def test_money_custom_currency(self) -> None:
        """Test Money accepts custom currency codes."""
        money = ItemMoney(Decimal("10.00"), "EUR")
        assert money.currency == "EUR"

    def test_money_addition(self) -> None:
        """Test Money addition."""
        money1 = ItemMoney(Decimal("10.00"), "BRL")
        money2 = ItemMoney(Decimal("20.00"), "BRL")
        result = money1 + money2
        assert result.amount == Decimal("30.00")

    def test_money_addition_different_currencies_rejected(self) -> None:
        """Test Money addition with different currencies is rejected."""
        money1 = ItemMoney(Decimal("10.00"), "BRL")
        money2 = ItemMoney(Decimal("20.00"), "USD")
        with pytest.raises(ValueError, match="Cannot operate on different currencies"):
            money1 + money2

    def test_money_multiplication(self) -> None:
        """Test Money multiplication by quantity."""
        money = ItemMoney(Decimal("10.00"), "BRL")
        result = money * 5
        assert result.amount == Decimal("50.00")

    def test_money_serialization(self) -> None:
        """Test Money can be serialized via dataclass fields."""
        money = ItemMoney(Decimal("99.90"), "BRL")
        # Money is a frozen dataclass, access fields directly
        assert str(money.amount) == "99.90"
        assert money.currency == "BRL"


class TestItemExampleEntity:
    """Tests for ItemExample entity."""

    def test_create_item(self) -> None:
        """Test ItemExample creation via factory method."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
            quantity=10,
        )
        assert item.name == "Widget"
        assert item.description == "A useful widget"
        assert item.sku == "WDG-001"
        assert item.quantity == 10
        assert item.status == ItemExampleStatus.ACTIVE

    def test_create_item_emits_event(self) -> None:
        """Test ItemExample creation emits ItemExampleCreated event."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )
        events = item.events
        assert len(events) == 1
        assert isinstance(events[0], ItemExampleCreated)
        assert events[0].name == "Widget"

    def test_update_item(self) -> None:
        """Test ItemExample update."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )
        item.clear_events()

        item.update(name="Updated Widget", quantity=5)

        assert item.name == "Updated Widget"
        assert item.quantity == 5
        events = item.events
        assert len(events) == 1
        assert isinstance(events[0], ItemExampleUpdated)

    def test_update_item_no_changes(self) -> None:
        """Test ItemExample update with no changes emits no event."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )
        item.clear_events()

        item.update(name="Widget")  # Same name

        events = item.events
        assert len(events) == 0

    def test_soft_delete(self) -> None:
        """Test ItemExample soft delete."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )
        item.clear_events()

        item.soft_delete()

        assert item.is_deleted is True
        events = item.events
        assert len(events) == 1
        assert isinstance(events[0], ItemExampleDeleted)

    def test_deactivate(self) -> None:
        """Test ItemExample deactivation."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )

        item.deactivate()

        assert item.status == ItemExampleStatus.INACTIVE

    def test_discontinue(self) -> None:
        """Test ItemExample discontinuation."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )

        item.discontinue()

        assert item.status == ItemExampleStatus.DISCONTINUED

    def test_is_available(self) -> None:
        """Test ItemExample availability check."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
            quantity=10,
        )

        assert item.is_available is True

        item.quantity = 0
        item._update_status_from_quantity()
        assert item.is_available is False

    def test_total_value(self) -> None:
        """Test ItemExample total value calculation."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("10.00")),
            sku="WDG-001",
            quantity=5,
        )

        total = item.total_value
        assert total.amount == Decimal("50.00")

    def test_clear_events(self) -> None:
        """Test clearing domain events."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
        )
        assert len(item.events) == 1

        item.clear_events()

        assert len(item.events) == 0

    def test_status_update_from_quantity_out_of_stock(self) -> None:
        """Test status updates to OUT_OF_STOCK when quantity reaches 0."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
            quantity=10,
        )
        item.clear_events()

        item.update(quantity=0)

        assert item.status == ItemExampleStatus.OUT_OF_STOCK

    def test_status_update_from_quantity_back_to_active(self) -> None:
        """Test status updates back to ACTIVE when quantity increases from 0."""
        item = ItemExample.create(
            name="Widget",
            description="A useful widget",
            price=ItemMoney(Decimal("99.90")),
            sku="WDG-001",
            quantity=0,
        )
        item.status = ItemExampleStatus.OUT_OF_STOCK
        item.clear_events()

        item.update(quantity=10)

        assert item.status == ItemExampleStatus.ACTIVE
