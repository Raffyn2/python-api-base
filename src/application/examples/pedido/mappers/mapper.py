"""Mapper for PedidoExample.

Implements BaseMapper for entity-DTO transformations with reduced duplication.

**Feature: application-common-integration**
**Feature: mapper-consolidation-2025**
**Validates: Requirements 4.2, 4.3**
"""

from application.common.mappers import IMapper
from application.common.mappers.base_mapper import BaseMapper
from application.examples.pedido.dtos import (
    PedidoExampleResponse,
    PedidoItemResponse,
)
from application.examples.shared.dtos import MoneyDTO
from domain.examples.pedido.entity import PedidoExample, PedidoItemExample


class PedidoItemMapper:
    """Mapper for PedidoItemExample entity to DTOs."""

    @staticmethod
    def to_response(entity: PedidoItemExample) -> PedidoItemResponse:
        """Map PedidoItemExample entity to response DTO."""
        return PedidoItemResponse(
            id=entity.id,
            item_id=entity.item_id,
            item_name=entity.item_name,
            quantity=entity.quantity,
            unit_price=MoneyDTO(
                amount=entity.unit_price.amount,
                currency=entity.unit_price.currency,
            ),
            discount=entity.discount,
            subtotal=MoneyDTO(
                amount=entity.subtotal.amount,
                currency=entity.subtotal.currency,
            ),
            total=MoneyDTO(
                amount=entity.total.amount,
                currency=entity.total.currency,
            ),
        )


class PedidoExampleMapper(BaseMapper, IMapper[PedidoExample, PedidoExampleResponse]):
    """Mapper for PedidoExample entity to DTOs.

    Inherits common list operations from BaseMapper to eliminate duplication.
    Only implements domain-specific conversions (to_dto, to_entity).
    """

    def to_dto(self, entity: PedidoExample) -> PedidoExampleResponse:
        """Map PedidoExample entity to response DTO."""
        return PedidoExampleResponse(
            id=entity.id,
            customer_id=entity.customer_id,
            customer_name=entity.customer_name,
            customer_email=entity.customer_email,
            status=entity.status.value,
            shipping_address=entity.shipping_address,
            notes=entity.notes,
            items=[PedidoItemMapper.to_response(i) for i in entity.items],
            items_count=entity.items_count,
            subtotal=MoneyDTO(
                amount=entity.subtotal.amount,
                currency=entity.subtotal.currency,
            ),
            total_discount=MoneyDTO(
                amount=entity.total_discount.amount,
                currency=entity.total_discount.currency,
            ),
            total=MoneyDTO(
                amount=entity.total.amount,
                currency=entity.total.currency,
            ),
            can_be_modified=entity.can_be_modified,
            can_be_cancelled=entity.can_be_cancelled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

    def to_entity(self, dto: PedidoExampleResponse) -> PedidoExample:
        """Map response DTO back to PedidoExample entity (for import)."""
        pedido = PedidoExample.create(
            customer_id=dto.customer_id,
            customer_name=dto.customer_name,
            customer_email=dto.customer_email,
            shipping_address=dto.shipping_address,
            notes=dto.notes,
            created_by=dto.created_by,
        )
        pedido._id = dto.id
        return pedido

    # Note: to_dto_list, to_entity_list are inherited from BaseMapper

    # Static methods for backward compatibility
    @staticmethod
    def to_response(entity: PedidoExample) -> PedidoExampleResponse:
        """Static method for backward compatibility."""
        return PedidoExampleMapper().to_dto(entity)

    @staticmethod
    def to_response_list(entities: list[PedidoExample]) -> list[PedidoExampleResponse]:
        """Static method for backward compatibility."""
        return PedidoExampleMapper().to_dto_list(entities)
