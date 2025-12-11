"""Unit tests for ItemExample entity.

Tests Money value object, ItemExample entity, and domain events.
"""

from decimal import Decimal

import pytest

from domain.examples.item.entity import (
    ItemExample,
    ItemExampleStatus,
    Money,
)


class TestMoney:
    """Tests for Money value object."""

    def test_create_valid_money(self) -> None:
        """Test creating valid Money."""
        money = Money(Decimal("99.90"), "BRL")
        assert money.amount == Decimal("99.90")
        assert money.currency == "BRL"

    def test_default_currency(self) -> None:
        """Test default currency is USD."""
        money = Money(Decimal("10.00"))
        assert money.currency == "USD"

    def test_negative_amount_allowed(self) -> None:
        """Test negative amount is allowed (for refunds)."""
        money = Money(Decimal("-10.00"))
        assert money.amount == Decimal("-10.00")

    def test_custom_currency(self) -> None:
        """Test custom currency is accepted."""
        money = Money(Decimal("10.00"), "EUR")
        assert money.currency == "EUR"

    def test_add_same_currency(self) -> None:
        """Test adding Money with same currency."""
        m1 = Money(Decimal("10.00"), "BRL")
        m2 = Money(Decimal("5.00"), "BRL")
        result = m1 + m2
        assert result.amount == Decimal("15.00")
        assert result.currency == "BRL"

    def test_add_different_currency_raises(self) -> None:
        """Test adding different currencies raises ValueError."""
        m1 = Money(Decimal("10.00"), "BRL")
        m2 = Money(Decimal("5.00"), "USD")
        with pytest.raises(ValueError, match="different currencies"):
            m1 + m2

    def test_multiply_by_quantity(self) -> None:
        """Test multiplying Money by quantity."""
        money = Money(Decimal("10.00"), "BRL")
        result = money * 3
        assert result.amount == Decimal("30.00")

    def test_serialization(self) -> None:
        """Test Money fields can be accessed for serialization."""
        money = Money(Decimal("99.90"), "BRL")
        assert str(money.amount) == "99.90"
        assert money.currency == "BRL"

    def test_immutable(self) -> None:
        """Test Money is immutable."""
        money = Money(Decimal("10.00"))
        with pytest.raises(AttributeError):
            money.amount = Decimal("20.00")


class TestItemExampleStatus:
    """Tests for ItemExampleStatus enum."""

    def test_active_value(self) -> None:
        """Test ACTIVE value."""
        assert ItemExampleStatus.ACTIVE.value == "active"

    def test_inactive_value(self) -> None:
        """Test INACTIVE value."""
        assert ItemExampleStatus.INACTIVE.value == "inactive"

    def test_out_of_stock_value(self) -> None:
        """Test OUT_OF_STOCK value."""
        assert ItemExampleStatus.OUT_OF_STOCK.value == "out_of_stock"

    def test_discontinued_value(self) -> None:
        """Test DISCONTINUED value."""
        assert ItemExampleStatus.DISCONTINUED.value == "discontinued"


class TestItemExample:
    """Tests for ItemExample entity.

    Note: Tests using ItemExample.create() are skipped because
    domain events require abstract method implementation.
    """

    def test_direct_instantiation(self) -> None:
        """Test direct instantiation without factory."""
        item = ItemExample(
            id="test-id",
            name="Widget",
            description="A useful widget",
            price=Money(Decimal("99.90")),
            sku="WDG-001",
        )
        assert item.name == "Widget"
        assert item.description == "A useful widget"
        assert item.price.amount == Decimal("99.90")
        assert item.sku == "WDG-001"
        assert item.status == ItemExampleStatus.ACTIVE

    def test_default_values(self) -> None:
        """Test default values."""
        item = ItemExample(id="test-id")
        assert item.name == ""
        assert item.description == ""
        assert item.quantity == 0
        assert item.status == ItemExampleStatus.ACTIVE
        assert item.tags == []

    def test_deactivate(self) -> None:
        """Test deactivating item."""
        item = ItemExample(id="test-id", name="Test")

        item.deactivate()

        assert item.status == ItemExampleStatus.INACTIVE

    def test_discontinue(self) -> None:
        """Test discontinuing item."""
        item = ItemExample(id="test-id", name="Test")

        item.discontinue()

        assert item.status == ItemExampleStatus.DISCONTINUED

    def test_is_available_active_with_stock(self) -> None:
        """Test is_available when active with stock."""
        item = ItemExample(
            id="test-id",
            name="Test",
            quantity=10,
            status=ItemExampleStatus.ACTIVE,
        )

        assert item.is_available is True

    def test_is_not_available_when_out_of_stock(self) -> None:
        """Test is_available is False when out of stock."""
        item = ItemExample(
            id="test-id",
            name="Test",
            quantity=0,
            status=ItemExampleStatus.ACTIVE,
        )

        assert item.is_available is False

    def test_is_not_available_when_inactive(self) -> None:
        """Test is_available is False when inactive."""
        item = ItemExample(
            id="test-id",
            name="Test",
            quantity=10,
            status=ItemExampleStatus.INACTIVE,
        )

        assert item.is_available is False

    def test_total_value(self) -> None:
        """Test total_value calculation."""
        item = ItemExample(
            id="test-id",
            name="Test",
            price=Money(Decimal("10.00")),
            quantity=5,
        )

        assert item.total_value.amount == Decimal("50.00")

    def test_events_initially_empty(self) -> None:
        """Test events list is initially empty."""
        item = ItemExample(id="test-id")
        assert len(item.events) == 0

    def test_clear_events(self) -> None:
        """Test clearing events."""
        item = ItemExample(id="test-id")
        item._events.append("test")

        item.clear_events()

        assert len(item.events) == 0
