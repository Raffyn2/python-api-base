"""Item use case implementation."""

from my_api.domain.entities.item import Item, ItemCreate, ItemResponse, ItemUpdate
from my_api.shared.mapper import IMapper
from my_api.shared.repository import IRepository
from my_api.shared.use_case import BaseUseCase


class ItemUseCase(BaseUseCase[Item, ItemCreate, ItemUpdate, ItemResponse]):
    """Use case for Item entity operations."""

    def __init__(
        self,
        repository: IRepository[Item, ItemCreate, ItemUpdate],
        mapper: IMapper[Item, ItemResponse],
    ) -> None:
        """Initialize Item use case."""
        super().__init__(repository, mapper, entity_name="Item")
