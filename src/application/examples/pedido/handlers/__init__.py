"""Pedido example handlers (Command/Query handlers).

**Feature: example-system-demo**
"""

from application.examples.pedido.handlers.handlers import (
    AddItemToPedidoCommandHandler,
    CancelPedidoCommandHandler,
    ConfirmPedidoCommandHandler,
    CreatePedidoCommandHandler,
    GetPedidoQueryHandler,
    IItemRepository,
    IPedidoRepository,
    ListPedidosQueryHandler,
)

__all__ = [
    "AddItemToPedidoCommandHandler",
    "CancelPedidoCommandHandler",
    "ConfirmPedidoCommandHandler",
    "CreatePedidoCommandHandler",
    "GetPedidoQueryHandler",
    "IItemRepository",
    "IPedidoRepository",
    "ListPedidosQueryHandler",
]
