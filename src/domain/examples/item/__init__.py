"""ItemExample bounded context.

**Feature: example-system-demo**
"""

from domain.examples.item.entity import (
    ItemExample,
    ItemExampleCreated,
    ItemExampleDeleted,
    ItemExampleStatus,
    ItemExampleUpdated,
    Money,
)
from domain.examples.item.specifications import (
    ItemExampleActiveSpec,
    ItemExampleAvailableSpec,
    ItemExampleCategorySpec,
    ItemExampleInStockSpec,
    ItemExamplePriceRangeSpec,
    ItemExampleTagSpec,
    available_items_in_category,
)

__all__ = [
    # Entity
    "ItemExample",
    # Specifications
    "ItemExampleActiveSpec",
    "ItemExampleAvailableSpec",
    "ItemExampleCategorySpec",
    # Events
    "ItemExampleCreated",
    "ItemExampleDeleted",
    "ItemExampleInStockSpec",
    "ItemExamplePriceRangeSpec",
    "ItemExampleStatus",
    "ItemExampleTagSpec",
    "ItemExampleUpdated",
    "Money",
    "available_items_in_category",
]
