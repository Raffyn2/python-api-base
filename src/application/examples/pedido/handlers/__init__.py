"""Pedido example handlers (Command/Query handlers).

**Feature: example-system-demo**
"""

from application.examples.pedido.handlers.handlers import (
    AddItemToPedidoCommandHandler,
    CancelPedidoCommandHandler,
    ConfirmPedidoCommandHandler,
    CreatePedidoCommandHandler,
    GetPedidoQueryHandler,
    ListPedidosQueryHandler,
)

__all__ = [
    "CreatePedidoCommandHandler",
    "AddItemToPedidoCommandHandler",
    "ConfirmPedidoCommandHandler",
    "CancelPedidoCommandHandler",
    "GetPedidoQueryHandler",
    "ListPedidosQueryHandler",
]
