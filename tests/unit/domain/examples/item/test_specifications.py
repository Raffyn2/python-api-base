"""Unit tests for ItemExample specifications.

Tests specification pattern implementations.
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


@pytest.fixture
def active_item() -> ItemExample:
    """Create active item with stock."""
    return ItemExample(
        id="act-001",
        name="Active Item",
        description="Test",
        price=Money(Decimal("50.00")),
        sku="ACT-001",
        quantity=10,
        category="Electronics",
        tags=["popular", "featured"],
        status=ItemExampleStatus.ACTIVE,
    )


@pytest.fixture
def inactive_item() -> ItemExample:
    """Create inactive item."""
    return ItemExample(
        id="ina-001",
        name="Inactive Item",
        description="Test",
        price=Money(Decimal("30.00")),
        sku="INA-001",
        quantity=5,
        status=ItemExampleStatus.INACTIVE,
    )


@pytest.fixture
def out_of_stock_item() -> ItemExample:
    """Create out of stock item."""
    return ItemExample(
        id="oos-001",
        name="Out of Stock",
        description="Test",
        price=Money(Decimal("25.00")),
        sku="OOS-001",
        quantity=0,
        status=ItemExampleStatus.ACTIVE,
    )


class TestItemExampleActiveSpec:
    """Tests for ItemExampleActiveSpec."""

    def test_active_item_satisfies(self, active_item: ItemExample) -> None:
        """Test active item satisfies spec."""
        spec = ItemExampleActiveSpec()
        assert spec.is_satisfied_by(active_item) is True

    def test_inactive_item_not_satisfies(self, inactive_item: ItemExample) -> None:
        """Test inactive item does not satisfy spec."""
        spec = ItemExampleActiveSpec()
        assert spec.is_satisfied_by(inactive_item) is False

    def test_deleted_item_not_satisfies(self, active_item: ItemExample) -> None:
        """Test deleted item does not satisfy spec."""
        active_item.mark_deleted()  # Use mark_deleted instead of soft_delete
        spec = ItemExampleActiveSpec()
        assert spec.is_satisfied_by(active_item) is False


class TestItemExampleInStockSpec:
    """Tests for ItemExampleInStockSpec."""

    def test_in_stock_satisfies(self, active_item: ItemExample) -> None:
        """Test item with stock satisfies spec."""
        spec = ItemExampleInStockSpec()
        assert spec.is_satisfied_by(active_item) is True

    def test_out_of_stock_not_satisfies(self, out_of_stock_item: ItemExample) -> None:
        """Test out of stock item does not satisfy spec."""
        spec = ItemExampleInStockSpec()
        assert spec.is_satisfied_by(out_of_stock_item) is False


class TestItemExamplePriceRangeSpec:
    """Tests for ItemExamplePriceRangeSpec."""

    def test_price_in_range_satisfies(self, active_item: ItemExample) -> None:
        """Test item with price in range satisfies spec."""
        spec = ItemExamplePriceRangeSpec(Decimal("0"), Decimal("100"))
        assert spec.is_satisfied_by(active_item) is True

    def test_price_below_range_not_satisfies(self, active_item: ItemExample) -> None:
        """Test item with price below range does not satisfy spec."""
        spec = ItemExamplePriceRangeSpec(Decimal("100"), Decimal("200"))
        assert spec.is_satisfied_by(active_item) is False

    def test_price_above_range_not_satisfies(self, active_item: ItemExample) -> None:
        """Test item with price above range does not satisfy spec."""
        spec = ItemExamplePriceRangeSpec(Decimal("0"), Decimal("10"))
        assert spec.is_satisfied_by(active_item) is False

    def test_price_at_boundary_satisfies(self) -> None:
        """Test item with price at boundary satisfies spec."""
        item = ItemExample(
            id="test-001",
            name="Test",
            description="Test",
            price=Money(Decimal("100.00")),
            sku="TST-001",
        )
        spec = ItemExamplePriceRangeSpec(Decimal("100"), Decimal("200"))
        assert spec.is_satisfied_by(item) is True


class TestItemExampleCategorySpec:
    """Tests for ItemExampleCategorySpec."""

    def test_matching_category_satisfies(self, active_item: ItemExample) -> None:
        """Test item in matching category satisfies spec."""
        spec = ItemExampleCategorySpec("Electronics")
        assert spec.is_satisfied_by(active_item) is True

    def test_different_category_not_satisfies(self, active_item: ItemExample) -> None:
        """Test item in different category does not satisfy spec."""
        spec = ItemExampleCategorySpec("Clothing")
        assert spec.is_satisfied_by(active_item) is False


class TestItemExampleTagSpec:
    """Tests for ItemExampleTagSpec."""

    def test_has_tag_satisfies(self, active_item: ItemExample) -> None:
        """Test item with tag satisfies spec."""
        spec = ItemExampleTagSpec("popular")
        assert spec.is_satisfied_by(active_item) is True

    def test_missing_tag_not_satisfies(self, active_item: ItemExample) -> None:
        """Test item without tag does not satisfy spec."""
        spec = ItemExampleTagSpec("sale")
        assert spec.is_satisfied_by(active_item) is False


class TestItemExampleAvailableSpec:
    """Tests for ItemExampleAvailableSpec."""

    def test_available_item_satisfies(self, active_item: ItemExample) -> None:
        """Test available item satisfies spec."""
        spec = ItemExampleAvailableSpec()
        assert spec.is_satisfied_by(active_item) is True

    def test_out_of_stock_not_satisfies(self, out_of_stock_item: ItemExample) -> None:
        """Test out of stock item does not satisfy spec."""
        spec = ItemExampleAvailableSpec()
        assert spec.is_satisfied_by(out_of_stock_item) is False


class TestCompositeSpecifications:
    """Tests for composite specification functions."""

    def test_available_items_in_category(self, active_item: ItemExample) -> None:
        """Test available_items_in_category composite spec."""
        spec = available_items_in_category("Electronics")
        assert spec.is_satisfied_by(active_item) is True

    def test_available_items_wrong_category(self, active_item: ItemExample) -> None:
        """Test available_items_in_category with wrong category."""
        spec = available_items_in_category("Clothing")
        assert spec.is_satisfied_by(active_item) is False

    def test_premium_items(self) -> None:
        """Test premium_items composite spec."""
        item = ItemExample(
            id="prm-001",
            name="Premium",
            description="Test",
            price=Money(Decimal("150.00")),
            sku="PRM-001",
            quantity=5,
            status=ItemExampleStatus.ACTIVE,
        )
        spec = premium_items(Decimal("100.00"))
        assert spec.is_satisfied_by(item) is True

    def test_premium_items_too_cheap(self, active_item: ItemExample) -> None:
        """Test premium_items with cheap item."""
        spec = premium_items(Decimal("100.00"))
        assert spec.is_satisfied_by(active_item) is False

    def test_clearance_items(self) -> None:
        """Test clearance_items composite spec."""
        item = ItemExample(
            id="clr-001",
            name="Clearance",
            description="Test",
            price=Money(Decimal("15.00")),
            sku="CLR-001",
            quantity=5,
            status=ItemExampleStatus.ACTIVE,
        )
        spec = clearance_items(Decimal("20.00"))
        assert spec.is_satisfied_by(item) is True

    def test_clearance_items_too_expensive(self, active_item: ItemExample) -> None:
        """Test clearance_items with expensive item."""
        spec = clearance_items(Decimal("20.00"))
        assert spec.is_satisfied_by(active_item) is False


class TestSpecificationOperators:
    """Tests for specification operators."""

    def test_and_operator(self, active_item: ItemExample) -> None:
        """Test AND operator (&)."""
        spec = ItemExampleActiveSpec() & ItemExampleInStockSpec()
        assert spec.is_satisfied_by(active_item) is True

    def test_or_operator(self, inactive_item: ItemExample) -> None:
        """Test OR operator (|)."""
        spec = ItemExampleActiveSpec() | ItemExampleInStockSpec()
        assert spec.is_satisfied_by(inactive_item) is True

    def test_not_operator(self, out_of_stock_item: ItemExample) -> None:
        """Test NOT operator (~)."""
        spec = ~ItemExampleInStockSpec()
        assert spec.is_satisfied_by(out_of_stock_item) is True
