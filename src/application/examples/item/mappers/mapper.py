"""Mapper for ItemExample.

Implements BaseMapper for entity-DTO transformations with reduced duplication.

**Feature: application-common-integration**
**Feature: mapper-consolidation-2025**
**Validates: Requirements 4.1, 4.3**
"""

from application.common.mappers import IMapper
from application.common.mappers.base_mapper import BaseMapper
from application.examples.item.dtos import ItemExampleResponse
from application.examples.shared.dtos import MoneyDTO
from domain.examples.item.entity import ItemExample, Money


class ItemExampleMapper(BaseMapper, IMapper[ItemExample, ItemExampleResponse]):
    """Mapper for ItemExample entity to DTOs.

    Inherits common list operations from BaseMapper to eliminate duplication.
    Only implements domain-specific conversions (to_dto, to_entity).
    """

    def to_dto(self, entity: ItemExample) -> ItemExampleResponse:
        """Map ItemExample entity to response DTO."""
        return ItemExampleResponse(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            sku=entity.sku,
            price=MoneyDTO(
                amount=entity.price.amount,
                currency=entity.price.currency,
            ),
            quantity=entity.quantity,
            status=entity.status.value,
            category=entity.category,
            tags=entity.tags,
            is_available=entity.is_available,
            total_value=MoneyDTO(
                amount=entity.total_value.amount,
                currency=entity.total_value.currency,
            ),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

    def to_entity(self, dto: ItemExampleResponse) -> ItemExample:
        """Map response DTO back to ItemExample entity (for import)."""
        return ItemExample(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            sku=dto.sku,
            price=Money(dto.price.amount, dto.price.currency),
            quantity=dto.quantity,
            category=dto.category,
            tags=list(dto.tags),
            created_by=dto.created_by,
        )

    # Note: to_dto_list, to_entity_list are inherited from BaseMapper

    # Static methods for backward compatibility
    @staticmethod
    def to_response(entity: ItemExample) -> ItemExampleResponse:
        """Static method for backward compatibility."""
        return ItemExampleMapper().to_dto(entity)

    @staticmethod
    def to_response_list(entities: list[ItemExample]) -> list[ItemExampleResponse]:
        """Static method for backward compatibility."""
        return ItemExampleMapper().to_dto_list(entities)
