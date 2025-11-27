"""Item mapper implementation."""

from my_api.domain.entities.item import Item, ItemResponse
from my_api.shared.mapper import IMapper


class ItemMapper(IMapper[Item, ItemResponse]):
    """Mapper for Item entity to ItemResponse DTO."""

    def to_dto(self, entity: Item) -> ItemResponse:
        """Convert Item entity to ItemResponse DTO."""
        return ItemResponse.model_validate(entity)

    def to_entity(self, dto: ItemResponse) -> Item:
        """Convert ItemResponse DTO to Item entity."""
        return Item.model_validate(dto.model_dump())
