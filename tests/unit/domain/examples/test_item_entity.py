"""Unit tests for domain/examples/item/entity.py.

Tests Item entity creation and validation.

**Task 9.1: Create tests for Item entity**
**Requirements: 2.3**
"""

from decimal import Decimal

import pytest

from domain.examples.item.entity import (
    ItemExample,
    ItemExampleCreated,
    ItemExampleDeleted,
    ItemExampleStatus,
    ItemExampleUpdated,
    Money,
)


class TestMoney:
    """Tests for Money value object."""

    def test_create_money(self) -> None:
        """Test creating money."""
        money = Money(Decimal("99.99"), "USD")
        assert money.amount == Decimal("99.99")
        assert money.currency == "USD"

    def test_default_currency(self) -> None:
        """Test default currency is USD."""
        money = Money(Decimal(100))
        assert money.currency == "USD"

    def test_negative_amount_allowed(self) -> None:
        """Test negative amount is allowed (for refunds)."""
        money = Money(Decimal(-10))
        assert money.amount == Decimal("-10.00")

    def test_custom_currency(self) -> None:
        """Test custom currency is accepted."""
        money = Money(Decimal(100), "EUR")
        assert money.currency == "EUR"

    def test_add_same_currency(self) -> None:
        """Test adding money with same currency."""
        m1 = Money(Decimal(50), "USD")
        m2 = Money(Decimal(30), "USD")
        result = m1 + m2
        assert result.amount == Decimal(80)
        assert result.currency == "USD"

    def test_add_different_currency_raises(self) -> None:
        """Test adding different currencies raises."""
        m1 = Money(Decimal(50), "USD")
        m2 = Money(Decimal(30), "EUR")
        with pytest.raises(ValueError, match="different currencies"):
            m1 + m2

    def test_multiply_by_quantity(self) -> None:
        """Test multiplying by quantity."""
        money = Money(Decimal(25), "USD")
        result = money * 4
        assert result.amount == Decimal(100)

    def test_serialization(self) -> None:
        """Test Money fields can be accessed for serialization."""
        money = Money(Decimal("99.99"), "USD")
        assert str(money.amount) == "99.99"
        assert money.currency == "USD"


class TestItemExampleCreate:
    """Tests for ItemExample.create factory method."""

    def test_create_item(self) -> None:
        """Test creating an item."""
        item = ItemExample.create(
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

    def test_create_with_optional_fields(self) -> None:
        """Test creating item with optional fields."""
        item = ItemExample.create(
            name="Widget",
            description="A widget",
            price=Money(Decimal(50)),
            sku="WDG-002",
            quantity=100,
            category="Electronics",
            tags=["popular", "sale"],
        )

        assert item.quantity == 100
        assert item.category == "Electronics"
        assert "popular" in item.tags

    def test_create_emits_event(self) -> None:
        """Test create emits ItemExampleCreated event."""
        item = ItemExample.create(
            name="Widget",
            description="A widget",
            price=Money(Decimal(50)),
            sku="WDG-003",
        )

        events = item.events
        assert len(events) == 1
        assert isinstance(events[0], ItemExampleCreated)
        assert events[0].name == "Widget"


class TestItemExampleUpdate:
    """Tests for ItemExample.update method."""

    def test_update_name(self) -> None:
        """Test updating item name."""
        item = ItemExample.create(
            name="Old Name",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
        )
        item.clear_events()

        item.update(name="New Name")

        assert item.name == "New Name"

    def test_update_emits_event(self) -> None:
        """Test update emits ItemExampleUpdated event."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
        )
        item.clear_events()

        item.update(name="Updated Widget")

        events = item.events
        assert len(events) == 1
        assert isinstance(events[0], ItemExampleUpdated)
        assert "name" in events[0].changes

    def test_update_quantity_changes_status(self) -> None:
        """Test updating quantity to 0 changes status to OUT_OF_STOCK."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
            quantity=10,
        )

        item.update(quantity=0)

        assert item.status == ItemExampleStatus.OUT_OF_STOCK


class TestItemExampleStatusTransitions:
    """Tests for ItemExample status transitions."""

    def test_deactivate(self) -> None:
        """Test deactivating item."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
        )

        item.deactivate()

        assert item.status == ItemExampleStatus.INACTIVE

    def test_discontinue(self) -> None:
        """Test discontinuing item."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
        )

        item.discontinue()

        assert item.status == ItemExampleStatus.DISCONTINUED

    def test_soft_delete(self) -> None:
        """Test soft deleting item."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
        )
        item.clear_events()

        item.soft_delete()

        assert item.is_deleted is True
        events = item.events
        assert any(isinstance(e, ItemExampleDeleted) for e in events)


class TestItemExampleProperties:
    """Tests for ItemExample computed properties."""

    def test_is_available(self) -> None:
        """Test is_available property."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
            quantity=10,
        )

        assert item.is_available is True

    def test_is_available_false_when_no_stock(self) -> None:
        """Test is_available is False when no stock."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(50)),
            sku="SKU-001",
            quantity=0,
        )

        assert item.is_available is False

    def test_total_value(self) -> None:
        """Test total_value property."""
        item = ItemExample.create(
            name="Widget",
            description="Desc",
            price=Money(Decimal(25)),
            sku="SKU-001",
            quantity=4,
        )

        assert item.total_value.amount == Decimal(100)
