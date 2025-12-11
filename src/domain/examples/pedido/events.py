"""Domain events for PedidoExample aggregate.

Contains all domain events related to order lifecycle.

**Feature: example-system-demo**
**Refactored: Extracted from entity.py for SRP compliance**
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from core.base.events.domain_event import DomainEvent
from core.shared.utils.datetime import utc_now

__all__ = [
    "PedidoCancelled",
    "PedidoCompleted",
    "PedidoCreated",
    "PedidoItemAdded",
]


@dataclass(frozen=True, kw_only=True)
class PedidoCreated(DomainEvent):
    """Event raised when a PedidoExample is created."""

    pedido_id: str
    customer_id: str
    occurred_at: datetime = field(default_factory=utc_now)

    @property
    def event_type(self) -> str:
        return "pedido.created"


@dataclass(frozen=True, kw_only=True)
class PedidoItemAdded(DomainEvent):
    """Event raised when an item is added to order."""

    pedido_id: str
    item_id: str
    quantity: int
    unit_price: Decimal
    occurred_at: datetime = field(default_factory=utc_now)

    @property
    def event_type(self) -> str:
        return "pedido.item_added"


@dataclass(frozen=True, kw_only=True)
class PedidoCompleted(DomainEvent):
    """Event raised when order is completed."""

    pedido_id: str
    total: Decimal
    items_count: int
    occurred_at: datetime = field(default_factory=utc_now)

    @property
    def event_type(self) -> str:
        return "pedido.completed"


@dataclass(frozen=True, kw_only=True)
class PedidoCancelled(DomainEvent):
    """Event raised when order is cancelled."""

    pedido_id: str
    reason: str
    occurred_at: datetime = field(default_factory=utc_now)

    @property
    def event_type(self) -> str:
        return "pedido.cancelled"
