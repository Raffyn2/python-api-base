"""Repositories for ItemExample and PedidoExample (facade module).

Re-exports repositories from dedicated modules for backward compatibility.

**Feature: example-system-demo**
**Refactored: Split into item_example.py and pedido_example.py for SRP**
"""

from infrastructure.db.repositories.item_example import ItemExampleRepository
from infrastructure.db.repositories.pedido_example import PedidoExampleRepository

__all__ = [
    "ItemExampleRepository",
    "PedidoExampleRepository",
]
