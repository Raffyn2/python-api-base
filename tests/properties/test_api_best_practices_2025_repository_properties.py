"""Property-based tests for Repository CRUD consistency.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

Property tests for:
- Property 7: CRUD Round-trip Consistency
- Property 8: Repository Idempotency
"""

from dataclasses import dataclass, field
from typing import Any
from collections.abc import Sequence
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel


# === Test Models ===


class SampleCreateDTO(BaseModel):
    """DTO for creating sample entities."""

    name: str
    value: int
    active: bool = True


class SampleUpdateDTO(BaseModel):
    """DTO for updating sample entities."""

    name: str | None = None
    value: int | None = None
    active: bool | None = None


class SampleEntity(BaseModel):
    """Sample entity for testing."""

    id: str
    name: str
    value: int
    active: bool = True


# === In-Memory Repository for Testing ===


class InMemoryRepository:
    """Simple in-memory repository for testing CRUD properties.

    **Feature: api-best-practices-review-2025**
    """

    def __init__(self) -> None:
        self._storage: dict[str, SampleEntity] = {}

    async def get_by_id(self, entity_id: str) -> SampleEntity | None:
        """Get entity by ID."""
        return self._storage.get(entity_id)

    async def create(self, data: SampleCreateDTO) -> SampleEntity:
        """Create new entity."""
        entity_id = str(uuid4())
        entity = SampleEntity(
            id=entity_id,
            name=data.name,
            value=data.value,
            active=data.active,
        )
        self._storage[entity_id] = entity
        return entity

    async def update(
        self, entity_id: str, data: SampleUpdateDTO
    ) -> SampleEntity | None:
        """Update existing entity."""
        entity = self._storage.get(entity_id)
        if entity is None:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        updated = entity.model_copy(update=update_dict)
        self._storage[entity_id] = updated
        return updated

    async def delete(self, entity_id: str) -> bool:
        """Delete entity."""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[SampleEntity]:
        """List all entities with pagination."""
        items = list(self._storage.values())
        return items[skip : skip + limit]

    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        return entity_id in self._storage

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities."""
        return len(self._storage)

    def clear(self) -> None:
        """Clear all storage."""
        self._storage.clear()


# === Strategies ===


name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
).filter(lambda x: x.strip() != "")

value_strategy = st.integers(min_value=-1000000, max_value=1000000)

create_dto_strategy = st.builds(
    SampleCreateDTO,
    name=name_strategy,
    value=value_strategy,
    active=st.booleans(),
)


# === Test Fixtures ===


@pytest.fixture
def repository() -> InMemoryRepository:
    """Fresh repository for each test."""
    return InMemoryRepository()


# === Property Tests ===


class TestCRUDRoundTrip:
    """Property 7: CRUD Round-trip Consistency.

    For any entity created, the retrieved entity SHALL match the creation data.
    For any entity updated, the retrieved entity SHALL reflect the updates.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    @settings(max_examples=50, deadline=None)
    @given(create_dto=create_dto_strategy)
    @pytest.mark.asyncio
    async def test_create_then_get_returns_same_data(
        self, create_dto: SampleCreateDTO
    ) -> None:
        """Created entity SHALL be retrievable with same data.

        **Feature: api-best-practices-review-2025, Property 7: CRUD Round-trip**
        **Validates: Requirements 4.1**
        """
        repo = InMemoryRepository()
        
        # Create
        created = await repo.create(create_dto)
        
        # Verify ID was assigned
        assert created.id is not None
        assert len(created.id) > 0
        
        # Get
        retrieved = await repo.get_by_id(created.id)
        
        # Verify round-trip consistency
        assert retrieved is not None
        assert retrieved.name == create_dto.name
        assert retrieved.value == create_dto.value
        assert retrieved.active == create_dto.active

    @settings(max_examples=50, deadline=None)
    @given(
        create_dto=create_dto_strategy,
        new_name=name_strategy,
        new_value=value_strategy,
    )
    @pytest.mark.asyncio
    async def test_update_reflects_changes(
        self,
        create_dto: SampleCreateDTO,
        new_name: str,
        new_value: int,
    ) -> None:
        """Updated entity SHALL reflect the changes.

        **Feature: api-best-practices-review-2025, Property 7**
        **Validates: Requirements 4.2**
        """
        repo = InMemoryRepository()
        
        # Create
        created = await repo.create(create_dto)
        
        # Update
        update_dto = SampleUpdateDTO(name=new_name, value=new_value)
        updated = await repo.update(created.id, update_dto)
        
        # Verify update
        assert updated is not None
        assert updated.name == new_name
        assert updated.value == new_value
        
        # Get and verify persistence
        retrieved = await repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.name == new_name
        assert retrieved.value == new_value

    @settings(max_examples=50, deadline=None)
    @given(create_dto=create_dto_strategy)
    @pytest.mark.asyncio
    async def test_delete_removes_entity(
        self, create_dto: SampleCreateDTO
    ) -> None:
        """Deleted entity SHALL not be retrievable.

        **Feature: api-best-practices-review-2025, Property 7**
        **Validates: Requirements 4.3**
        """
        repo = InMemoryRepository()
        
        # Create
        created = await repo.create(create_dto)
        
        # Verify exists
        assert await repo.exists(created.id) is True
        
        # Delete
        deleted = await repo.delete(created.id)
        assert deleted is True
        
        # Verify not exists
        assert await repo.exists(created.id) is False
        retrieved = await repo.get_by_id(created.id)
        assert retrieved is None


class TestRepositoryIdempotency:
    """Property 8: Repository Idempotency.

    For any entity, delete operations SHALL be idempotent.
    Getting a non-existent entity SHALL return None (not raise).

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 4.4, 4.5**
    """

    @settings(max_examples=50, deadline=None)
    @given(create_dto=create_dto_strategy)
    @pytest.mark.asyncio
    async def test_delete_idempotent(
        self, create_dto: SampleCreateDTO
    ) -> None:
        """Delete SHALL be idempotent (second delete returns False).

        **Feature: api-best-practices-review-2025, Property 8**
        **Validates: Requirements 4.4**
        """
        repo = InMemoryRepository()
        
        # Create
        created = await repo.create(create_dto)
        
        # First delete succeeds
        first_delete = await repo.delete(created.id)
        assert first_delete is True
        
        # Second delete returns False (not error)
        second_delete = await repo.delete(created.id)
        assert second_delete is False
        
        # Third delete also False
        third_delete = await repo.delete(created.id)
        assert third_delete is False

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self) -> None:
        """Get non-existent entity SHALL return None, not raise.

        **Feature: api-best-practices-review-2025, Property 8**
        **Validates: Requirements 4.5**
        """
        repo = InMemoryRepository()
        
        # Get non-existent
        result = await repo.get_by_id("non-existent-id")
        assert result is None
        
        # Exists returns False
        exists = await repo.exists("non-existent-id")
        assert exists is False

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self) -> None:
        """Update non-existent entity SHALL return None, not raise.

        **Feature: api-best-practices-review-2025, Property 8**
        **Validates: Requirements 4.5**
        """
        repo = InMemoryRepository()
        
        # Update non-existent
        update_dto = SampleUpdateDTO(name="new name")
        result = await repo.update("non-existent-id", update_dto)
        assert result is None


class TestRepositoryPagination:
    """Tests for repository pagination.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 4.6**
    """

    @settings(max_examples=20, deadline=None)
    @given(count=st.integers(min_value=1, max_value=20))
    @pytest.mark.asyncio
    async def test_list_all_returns_correct_count(self, count: int) -> None:
        """List all SHALL return correct number of entities.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 4.6**
        """
        repo = InMemoryRepository()
        
        # Create entities
        for i in range(count):
            dto = SampleCreateDTO(name=f"item-{i}", value=i)
            await repo.create(dto)
        
        # List all
        items = await repo.list_all()
        assert len(items) == count

    @settings(max_examples=20, deadline=None)
    @given(
        count=st.integers(min_value=5, max_value=20),
        skip=st.integers(min_value=0, max_value=10),
        limit=st.integers(min_value=1, max_value=10),
    )
    @pytest.mark.asyncio
    async def test_pagination_respects_skip_and_limit(
        self, count: int, skip: int, limit: int
    ) -> None:
        """Pagination SHALL respect skip and limit.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 4.6**
        """
        repo = InMemoryRepository()
        
        # Create entities
        for i in range(count):
            dto = SampleCreateDTO(name=f"item-{i}", value=i)
            await repo.create(dto)
        
        # List with pagination
        items = await repo.list_all(skip=skip, limit=limit)
        
        # Verify pagination
        expected_count = min(limit, max(0, count - skip))
        assert len(items) == expected_count


class TestRepositoryCount:
    """Tests for repository count.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 4.6**
    """

    @settings(max_examples=20, deadline=None)
    @given(count=st.integers(min_value=0, max_value=20))
    @pytest.mark.asyncio
    async def test_count_matches_actual(self, count: int) -> None:
        """Count SHALL match actual number of entities.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 4.6**
        """
        repo = InMemoryRepository()
        
        # Empty repository
        assert await repo.count() == 0
        
        # Create entities
        for i in range(count):
            dto = SampleCreateDTO(name=f"item-{i}", value=i)
            await repo.create(dto)
        
        # Count matches
        assert await repo.count() == count

    @settings(max_examples=10, deadline=None)
    @given(create_count=st.integers(min_value=3, max_value=10))
    @pytest.mark.asyncio
    async def test_count_updates_after_delete(self, create_count: int) -> None:
        """Count SHALL update after delete.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 4.6**
        """
        repo = InMemoryRepository()
        
        # Create entities
        created_ids: list[str] = []
        for i in range(create_count):
            dto = SampleCreateDTO(name=f"item-{i}", value=i)
            entity = await repo.create(dto)
            created_ids.append(entity.id)
        
        assert await repo.count() == create_count
        
        # Delete first entity
        await repo.delete(created_ids[0])
        assert await repo.count() == create_count - 1
        
        # Delete another
        await repo.delete(created_ids[1])
        assert await repo.count() == create_count - 2


class TestPartialUpdate:
    """Tests for partial update behavior.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 4.2**
    """

    @settings(max_examples=50, deadline=None)
    @given(
        create_dto=create_dto_strategy,
        new_name=name_strategy,
    )
    @pytest.mark.asyncio
    async def test_partial_update_preserves_other_fields(
        self, create_dto: SampleCreateDTO, new_name: str
    ) -> None:
        """Partial update SHALL preserve unspecified fields.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 4.2**
        """
        repo = InMemoryRepository()
        
        # Create
        created = await repo.create(create_dto)
        original_value = created.value
        original_active = created.active
        
        # Partial update (only name)
        update_dto = SampleUpdateDTO(name=new_name)
        updated = await repo.update(created.id, update_dto)
        
        # Verify partial update
        assert updated is not None
        assert updated.name == new_name  # Changed
        assert updated.value == original_value  # Preserved
        assert updated.active == original_active  # Preserved
