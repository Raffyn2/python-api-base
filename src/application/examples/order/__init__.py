"""Order example module.

Demonstrates the UseCase pattern for complex business operations.

**Feature: architecture-consolidation-2025**
"""

from application.examples.order.dtos import (
    OrderItemInput,
    OrderItemOutput,
    PlaceOrderInput,
    PlaceOrderOutput,
)
from application.examples.order.use_cases import PlaceOrderUseCase

__all__ = [
    # DTOs
    "OrderItemInput",
    "OrderItemOutput",
    "PlaceOrderInput",
    "PlaceOrderOutput",
    # Use Case
    "PlaceOrderUseCase",
]
