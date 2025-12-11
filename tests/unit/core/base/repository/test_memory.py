"""Tests for core/base/repository/memory.py - In-memory repository."""

import pytest
from pydantic import BaseModel

from src.core.base.repository.memory import InMemoryRepository


class SampleEntity(BaseModel):
    """Sample entity for repository tests."""

    id: str | None = None
    name: str
    value: int = 0
    is_deleted: bool = False


class CreateSampleEntity(BaseModel):
    """DTO for creating sample entity."""

    name: str
    value: int = 0


class UpdateSampleEntity(BaseModel):
    """DTO for updating sample entity."""

    name: str | None = None
    value: int | None = None


class TestInMemoryRepositoryInit:
    """Tests for InMemoryRepository initialization."""

    def test_init_creates_empty_storage(self):
        repo = InMemoryRepository(SampleEntity)
        assert len(repo._storage) == 0

    def test_init_with_entity_type(self):
        repo = InMemoryRepository(SampleEntity)
        assert repo._entity_type == SampleEntity

    def test_init_counter_starts_at_zero(self):
        repo = InMemoryRepository(SampleEntity)
        assert repo._counter == 0


class TestInMemoryRepositoryCreate:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_returns_entity(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="test", value=10)
        entity = await repo.create(data)
        assert isinstance(entity, SampleEntity)

    @pytest.mark.asyncio
    async def test_create_generates_id(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="test", value=10)
        entity = await repo.create(data)
        assert entity.id is not None

    @pytest.mark.asyncio
    async def test_create_stores_entity(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="test", value=10)
        entity = await repo.create(data)
        assert entity.id in repo._storage

    @pytest.mark.asyncio
    async def test_create_preserves_data(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="myname", value=42)
        entity = await repo.create(data)
        assert entity.name == "myname"
        assert entity.value == 42

    @pytest.mark.asyncio
    async def test_create_increments_counter(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="test", value=10)
        await repo.create(data)
        assert repo._counter == 1

    @pytest.mark.asyncio
    async def test_create_multiple_unique_ids(self):
        repo = InMemoryRepository(SampleEntity)
        entity1 = await repo.create(CreateSampleEntity(name="one", value=1))
        entity2 = await repo.create(CreateSampleEntity(name="two", value=2))
        assert entity1.id != entity2.id


class TestInMemoryRepositoryGetById:
    """Tests for get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="test", value=10)
        created = await repo.create(data)
        entity = await repo.get_by_id(created.id)
        assert entity is not None
        assert entity.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self):
        repo = InMemoryRepository(SampleEntity)
        entity = await repo.get_by_id("nonexistent")
        assert entity is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(self):
        repo = InMemoryRepository(SampleEntity)
        data = CreateSampleEntity(name="test", value=10)
        created = await repo.create(data)
        await repo.delete(created.id, soft=True)
        entity = await repo.get_by_id(created.id)
        assert entity is None


class TestInMemoryRepositoryGetAll:
    """Tests for get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_returns_empty_list(self):
        repo = InMemoryRepository(SampleEntity)
        entities, total = await repo.get_all()
        assert entities == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_all_returns_all_entities(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="one", value=1))
        await repo.create(CreateSampleEntity(name="two", value=2))
        entities, total = await repo.get_all()
        assert len(entities) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_get_all_with_skip(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="one", value=1))
        await repo.create(CreateSampleEntity(name="two", value=2))
        await repo.create(CreateSampleEntity(name="three", value=3))
        entities, total = await repo.get_all(skip=1)
        assert len(entities) == 2
        assert total == 3

    @pytest.mark.asyncio
    async def test_get_all_with_limit(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="one", value=1))
        await repo.create(CreateSampleEntity(name="two", value=2))
        await repo.create(CreateSampleEntity(name="three", value=3))
        entities, total = await repo.get_all(limit=2)
        assert len(entities) == 2
        assert total == 3

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="one", value=10))
        await repo.create(CreateSampleEntity(name="two", value=20))
        entities, _total = await repo.get_all(filters={"value": 10})
        assert len(entities) == 1
        assert entities[0].value == 10

    @pytest.mark.asyncio
    async def test_get_all_excludes_soft_deleted(self):
        repo = InMemoryRepository(SampleEntity)
        entity1 = await repo.create(CreateSampleEntity(name="one", value=1))
        await repo.create(CreateSampleEntity(name="two", value=2))
        await repo.delete(entity1.id, soft=True)
        entities, total = await repo.get_all()
        assert len(entities) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_all_with_sort_asc(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="c", value=3))
        await repo.create(CreateSampleEntity(name="a", value=1))
        await repo.create(CreateSampleEntity(name="b", value=2))
        entities, _ = await repo.get_all(sort_by="name", sort_order="asc")
        names = [e.name for e in entities]
        assert names == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_get_all_with_sort_desc(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="a", value=1))
        await repo.create(CreateSampleEntity(name="c", value=3))
        await repo.create(CreateSampleEntity(name="b", value=2))
        entities, _ = await repo.get_all(sort_by="name", sort_order="desc")
        names = [e.name for e in entities]
        assert names == ["c", "b", "a"]


class TestInMemoryRepositoryUpdate:
    """Tests for update method."""

    @pytest.mark.asyncio
    async def test_update_returns_updated_entity(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="original", value=10))
        updated = await repo.update(created.id, UpdateSampleEntity(name="updated"))
        assert updated is not None
        assert updated.name == "updated"

    @pytest.mark.asyncio
    async def test_update_preserves_unchanged_fields(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="original", value=10))
        updated = await repo.update(created.id, UpdateSampleEntity(name="updated"))
        assert updated.value == 10

    @pytest.mark.asyncio
    async def test_update_returns_none_for_missing(self):
        repo = InMemoryRepository(SampleEntity)
        updated = await repo.update("nonexistent", UpdateSampleEntity(name="test"))
        assert updated is None

    @pytest.mark.asyncio
    async def test_update_stores_changes(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="original", value=10))
        await repo.update(created.id, UpdateSampleEntity(value=99))
        entity = await repo.get_by_id(created.id)
        assert entity.value == 99


class TestInMemoryRepositoryDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_soft_delete_returns_true(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="test", value=10))
        result = await repo.delete(created.id, soft=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_soft_delete_marks_as_deleted(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="test", value=10))
        await repo.delete(created.id, soft=True)
        # Entity still in storage but marked deleted
        assert created.id in repo._storage
        assert repo._storage[created.id].is_deleted is True

    @pytest.mark.asyncio
    async def test_hard_delete_removes_entity(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="test", value=10))
        await repo.delete(created.id, soft=False)
        assert created.id not in repo._storage

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing(self):
        repo = InMemoryRepository(SampleEntity)
        result = await repo.delete("nonexistent")
        assert result is False


class TestInMemoryRepositoryExists:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="test", value=10))
        assert await repo.exists(created.id) is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing(self):
        repo = InMemoryRepository(SampleEntity)
        assert await repo.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_soft_deleted(self):
        repo = InMemoryRepository(SampleEntity)
        created = await repo.create(CreateSampleEntity(name="test", value=10))
        await repo.delete(created.id, soft=True)
        assert await repo.exists(created.id) is False


class TestInMemoryRepositoryCreateMany:
    """Tests for create_many method."""

    @pytest.mark.asyncio
    async def test_create_many_returns_list(self):
        repo = InMemoryRepository(SampleEntity)
        data = [
            CreateSampleEntity(name="one", value=1),
            CreateSampleEntity(name="two", value=2),
        ]
        entities = await repo.create_many(data)
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_create_many_stores_all(self):
        repo = InMemoryRepository(SampleEntity)
        data = [
            CreateSampleEntity(name="one", value=1),
            CreateSampleEntity(name="two", value=2),
            CreateSampleEntity(name="three", value=3),
        ]
        await repo.create_many(data)
        _, total = await repo.get_all()
        assert total == 3


class TestInMemoryRepositoryBulkUpdate:
    """Tests for bulk_update method."""

    @pytest.mark.asyncio
    async def test_bulk_update_returns_updated(self):
        repo = InMemoryRepository(SampleEntity)
        e1 = await repo.create(CreateSampleEntity(name="one", value=1))
        e2 = await repo.create(CreateSampleEntity(name="two", value=2))
        updates = [
            (e1.id, UpdateSampleEntity(value=10)),
            (e2.id, UpdateSampleEntity(value=20)),
        ]
        results = await repo.bulk_update(updates)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_bulk_update_skips_missing(self):
        repo = InMemoryRepository(SampleEntity)
        e1 = await repo.create(CreateSampleEntity(name="one", value=1))
        updates = [
            (e1.id, UpdateSampleEntity(value=10)),
            ("nonexistent", UpdateSampleEntity(value=20)),
        ]
        results = await repo.bulk_update(updates)
        assert len(results) == 1


class TestInMemoryRepositoryBulkDelete:
    """Tests for bulk_delete method."""

    @pytest.mark.asyncio
    async def test_bulk_delete_returns_count(self):
        repo = InMemoryRepository(SampleEntity)
        e1 = await repo.create(CreateSampleEntity(name="one", value=1))
        e2 = await repo.create(CreateSampleEntity(name="two", value=2))
        count = await repo.bulk_delete([e1.id, e2.id])
        assert count == 2

    @pytest.mark.asyncio
    async def test_bulk_delete_skips_missing(self):
        repo = InMemoryRepository(SampleEntity)
        e1 = await repo.create(CreateSampleEntity(name="one", value=1))
        count = await repo.bulk_delete([e1.id, "nonexistent"])
        assert count == 1


class TestInMemoryRepositoryClear:
    """Tests for clear method."""

    @pytest.mark.asyncio
    async def test_clear_removes_all(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="one", value=1))
        await repo.create(CreateSampleEntity(name="two", value=2))
        repo.clear()
        _, total = await repo.get_all()
        assert total == 0

    @pytest.mark.asyncio
    async def test_clear_resets_counter(self):
        repo = InMemoryRepository(SampleEntity)
        await repo.create(CreateSampleEntity(name="one", value=1))
        repo.clear()
        assert repo._counter == 0
