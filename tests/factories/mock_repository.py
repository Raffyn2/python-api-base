"""Mock repository factories for testing.

**Validates: Requirements 14.4**
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from unittest.mock import AsyncMock, MagicMock

from pydantic import BaseModel

from my_api.shared.repository import IRepository

T = TypeVar("T", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


class MockRepository(IRepository[T, CreateT, UpdateT], Generic[T, CreateT, UpdateT]):
    """Configurable mock repository for testing.
    
    Allows configuring return values and behaviors for each method.
    """

    def __init__(
        self,
        entity_type: type[T],
        *,
        get_by_id_return: T | None = None,
        get_all_return: tuple[Sequence[T], int] | None = None,
        create_return: T | None = None,
        update_return: T | None = None,
        delete_return: bool = True,
        exists_return: bool = True,
        create_many_return: Sequence[T] | None = None,
        raise_on_create: Exception | None = None,
        raise_on_update: Exception | None = None,
        raise_on_delete: Exception | None = None,
    ) -> None:
        """Initialize mock repository with configurable behavior.
        
        Args:
            entity_type: Type of entity this repository handles.
            get_by_id_return: Value to return from get_by_id.
            get_all_return: Value to return from get_all.
            create_return: Value to return from create.
            update_return: Value to return from update.
            delete_return: Value to return from delete.
            exists_return: Value to return from exists.
            create_many_return: Value to return from create_many.
            raise_on_create: Exception to raise on create.
            raise_on_update: Exception to raise on update.
            raise_on_delete: Exception to raise on delete.
        """
        self._entity_type = entity_type
        self._get_by_id_return = get_by_id_return
        self._get_all_return = get_all_return or ([], 0)
        self._create_return = create_return
        self._update_return = update_return
        self._delete_return = delete_return
        self._exists_return = exists_return
        self._create_many_return = create_many_return or []
        self._raise_on_create = raise_on_create
        self._raise_on_update = raise_on_update
        self._raise_on_delete = raise_on_delete
        
        # Track calls
        self.get_by_id_calls: list[str] = []
        self.get_all_calls: list[dict[str, Any]] = []
        self.create_calls: list[CreateT] = []
        self.update_calls: list[tuple[str, UpdateT]] = []
        self.delete_calls: list[str] = []
        self.exists_calls: list[str] = []
        self.create_many_calls: list[Sequence[CreateT]] = []

    async def get_by_id(self, id: str) -> T | None:
        """Get entity by ID."""
        self.get_by_id_calls.append(id)
        return self._get_by_id_return

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> tuple[Sequence[T], int]:
        """Get paginated list of entities."""
        self.get_all_calls.append({
            "skip": skip,
            "limit": limit,
            "filters": filters,
            "sort_by": sort_by,
            "sort_order": sort_order,
        })
        return self._get_all_return

    async def create(self, data: CreateT) -> T:
        """Create new entity."""
        self.create_calls.append(data)
        if self._raise_on_create:
            raise self._raise_on_create
        if self._create_return:
            return self._create_return
        # Create a default entity from the data
        return self._entity_type.model_validate(data.model_dump())

    async def update(self, id: str, data: UpdateT) -> T | None:
        """Update existing entity."""
        self.update_calls.append((id, data))
        if self._raise_on_update:
            raise self._raise_on_update
        return self._update_return

    async def delete(self, id: str, *, soft: bool = True) -> bool:
        """Delete entity."""
        self.delete_calls.append(id)
        if self._raise_on_delete:
            raise self._raise_on_delete
        return self._delete_return

    async def create_many(self, data: Sequence[CreateT]) -> Sequence[T]:
        """Bulk create entities."""
        self.create_many_calls.append(data)
        if self._create_many_return:
            return self._create_many_return
        return [self._entity_type.model_validate(d.model_dump()) for d in data]

    async def exists(self, id: str) -> bool:
        """Check if entity exists."""
        self.exists_calls.append(id)
        return self._exists_return

    def reset_calls(self) -> None:
        """Reset all call tracking."""
        self.get_by_id_calls.clear()
        self.get_all_calls.clear()
        self.create_calls.clear()
        self.update_calls.clear()
        self.delete_calls.clear()
        self.exists_calls.clear()
        self.create_many_calls.clear()


class MockRepositoryFactory:
    """Factory for creating mock repositories with common configurations."""

    @staticmethod
    def create_empty(entity_type: type[T]) -> MockRepository[T, Any, Any]:
        """Create a mock repository that returns empty/None for all queries."""
        return MockRepository(
            entity_type,
            get_by_id_return=None,
            get_all_return=([], 0),
            update_return=None,
            delete_return=False,
            exists_return=False,
        )

    @staticmethod
    def create_with_entity(
        entity_type: type[T],
        entity: T,
    ) -> MockRepository[T, Any, Any]:
        """Create a mock repository that returns the given entity."""
        return MockRepository(
            entity_type,
            get_by_id_return=entity,
            get_all_return=([entity], 1),
            create_return=entity,
            update_return=entity,
            delete_return=True,
            exists_return=True,
        )

    @staticmethod
    def create_with_entities(
        entity_type: type[T],
        entities: list[T],
    ) -> MockRepository[T, Any, Any]:
        """Create a mock repository with multiple entities."""
        return MockRepository(
            entity_type,
            get_by_id_return=entities[0] if entities else None,
            get_all_return=(entities, len(entities)),
            create_return=entities[0] if entities else None,
            update_return=entities[0] if entities else None,
            delete_return=True,
            exists_return=bool(entities),
            create_many_return=entities,
        )

    @staticmethod
    def create_failing(
        entity_type: type[T],
        exception: Exception,
    ) -> MockRepository[T, Any, Any]:
        """Create a mock repository that raises exceptions."""
        return MockRepository(
            entity_type,
            raise_on_create=exception,
            raise_on_update=exception,
            raise_on_delete=exception,
        )
