"""Unit tests for domain/examples/item/specifications.py.

Tests Item specifications.

**Task 9.2: Create tests for Item specifications**
**Requirements: 2.3**
"""

from decimal import Decimal

import pytest

from domain.examples.item.entity import ItemExample, ItemExampleStatus, Money
from domain.examples.item.specifications import (
    ItemExampleActiveSpec,
    ItemExampleAvailableSpec,
    ItemExampleCategorySpec,
    ItemExampleInStockSpec,
    ItemExamplePriceRangeSpec,
    ItemExampleTagSpec,
    available_items_in_category,
    clearance_items,
    premium_items,
)


def create_item(
    name: str = "Test",
    price: Decimal = Decimal("50"),
    quantity: int = 10,
    category: str = "General",
    tags: list[str] | None = None,
    status: ItemExampleStatus = ItemExampleStatus.ACTIVE,
) -> ItemExample:
    """Helper to create test items."""
    item = ItemExample.create(
        name=name,
        description="Test item",
        price=Money(price),
        sku=f"SKU-{name}",
        quantity=quantity,
        category=category,
        tags=tags or [],
    )
    if status != ItemExampleStatus.ACTIVE:
        item.status = status
    return item


class TestItemExampleActiveSpec:
    """Tests for ItemExampleActiveSpec."""

    def test_active_item_satisfies(self) -> None:
        """Test active item satisfies spec."""
        item = create_item()
        spec = ItemExampleActiveSpec()

        assert spec.is_satisfied_by(item) is True

    def test_inactive_item_not_satisfies(self) -> None:
        """Test inactive item doesn't satisfy spec."""
        item = create_item(status=ItemExampleStatus.INACTIVE)
        spec = ItemExampleActiveSpec()

        assert spec.is_satisfied_by(item) is False

    def test_deleted_item_not_satisfies(self) -> None:
        """Test deleted item doesn't satisfy spec."""
        item = create_item()
        item.soft_delete()
        spec = ItemExampleActiveSpec()

        assert spec.is_satisfied_by(item) is False


class TestItemExampleInStockSpec:
    """Tests for ItemExampleInStockSpec."""

    def test_in_stock_satisfies(self) -> None:
        """Test item with stock satisfies spec."""
        item = create_item(quantity=10)
        spec = ItemExampleInStockSpec()

        assert spec.is_satisfied_by(item) is True

    def test_no_stock_not_satisfies(self) -> None:
        """Test item without stock doesn't satisfy spec."""
        item = create_item(quantity=0)
        spec = ItemExampleInStockSpec()

        assert spec.is_satisfied_by(item) is False


class TestItemExamplePriceRangeSpec:
    """Tests for ItemExamplePriceRangeSpec."""

    def test_price_in_range_satisfies(self) -> None:
        """Test item with price in range satisfies spec."""
        item = create_item(price=Decimal("50"))
        spec = ItemExamplePriceRangeSpec(Decimal("10"), Decimal("100"))

        assert spec.is_satisfied_by(item) is True

    def test_price_below_range_not_satisfies(self) -> None:
        """Test item with price below range doesn't satisfy."""
        item = create_item(price=Decimal("5"))
        spec = ItemExamplePriceRangeSpec(Decimal("10"), Decimal("100"))

        assert spec.is_satisfied_by(item) is False

    def test_price_above_range_not_satisfies(self) -> None:
        """Test item with price above range doesn't satisfy."""
        item = create_item(price=Decimal("150"))
        spec = ItemExamplePriceRangeSpec(Decimal("10"), Decimal("100"))

        assert spec.is_satisfied_by(item) is False

    def test_price_at_boundary_satisfies(self) -> None:
        """Test item with price at boundary satisfies."""
        item = create_item(price=Decimal("100"))
        spec = ItemExamplePriceRangeSpec(Decimal("10"), Decimal("100"))

        assert spec.is_satisfied_by(item) is True


class TestItemExampleCategorySpec:
    """Tests for ItemExampleCategorySpec."""

    def test_matching_category_satisfies(self) -> None:
        """Test item with matching category satisfies spec."""
        item = create_item(category="Electronics")
        spec = ItemExampleCategorySpec("Electronics")

        assert spec.is_satisfied_by(item) is True

    def test_different_category_not_satisfies(self) -> None:
        """Test item with different category doesn't satisfy."""
        item = create_item(category="Clothing")
        spec = ItemExampleCategorySpec("Electronics")

        assert spec.is_satisfied_by(item) is False


class TestItemExampleTagSpec:
    """Tests for ItemExampleTagSpec."""

    def test_has_tag_satisfies(self) -> None:
        """Test item with tag satisfies spec."""
        item = create_item(tags=["popular", "sale"])
        spec = ItemExampleTagSpec("popular")

        assert spec.is_satisfied_by(item) is True

    def test_missing_tag_not_satisfies(self) -> None:
        """Test item without tag doesn't satisfy."""
        item = create_item(tags=["sale"])
        spec = ItemExampleTagSpec("popular")

        assert spec.is_satisfied_by(item) is False


class TestCompositeSpecifications:
    """Tests for composite specification functions."""

    def test_available_items_in_category(self) -> None:
        """Test available_items_in_category composite spec."""
        item = create_item(category="Electronics", quantity=10)
        spec = available_items_in_category("Electronics")

        assert spec.is_satisfied_by(item) is True

    def test_premium_items(self) -> None:
        """Test premium_items composite spec."""
        item = create_item(price=Decimal("150"), quantity=10)
        spec = premium_items(Decimal("100"))

        assert spec.is_satisfied_by(item) is True

    def test_premium_items_below_threshold(self) -> None:
        """Test premium_items rejects items below threshold."""
        item = create_item(price=Decimal("50"), quantity=10)
        spec = premium_items(Decimal("100"))

        assert spec.is_satisfied_by(item) is False

    def test_clearance_items(self) -> None:
        """Test clearance_items composite spec."""
        item = create_item(price=Decimal("15"), quantity=10)
        spec = clearance_items(Decimal("20"))

        assert spec.is_satisfied_by(item) is True
