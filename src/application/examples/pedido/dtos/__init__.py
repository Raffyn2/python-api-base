"""Pedido example DTOs (Data Transfer Objects).

**Feature: example-system-demo**
"""

from application.examples.pedido.dtos.dtos import (
    AddItemRequest,
    CancelPedidoRequest,
    ConfirmPedidoRequest,
    PedidoExampleCreate,
    PedidoExampleResponse,
    PedidoExampleUpdate,
    PedidoItemResponse,
    UpdateStatusRequest,
)

__all__ = [
    "AddItemRequest",
    "CancelPedidoRequest",
    "ConfirmPedidoRequest",
    "PedidoExampleCreate",
    "PedidoExampleUpdate",
    "PedidoExampleResponse",
    "PedidoItemResponse",
    "UpdateStatusRequest",
]
