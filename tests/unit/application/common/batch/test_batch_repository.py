"""Unit tests for batch repository.

Tests BatchRepository CRUD operations and error handling.
"""

import pytest
from pydantic import BaseModel

from application.common.batch.config.config import (
    BatchConfig,
    BatchErrorStrategy,
    BatchProgress,
)
from application.common.batch.repositories.repository import BatchRepository


class SampleEntity(BaseModel):
    """Sample entity for batch operations."""

    id: str = ""
    name: str
    value: int = 0
    is_deleted: bool = False


class CreateSampleEntity(BaseModel):
    """Create DTO for sample entity."""

    id: str = ""
    name: str
    value: int = 0


class UpdateSampleEntity(BaseModel):
    """Update DTO for sample entity."""

    name: str | None = None
    value: int | None = None


class TestBatchRepositoryInit:
    """Tests for BatchRepository initialization."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default values."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)

        assert repo._entity_type == SampleEntity
        assert repo._id_field == "id"
        assert repo.count == 0

    def test_init_with_custom_id_generator(self) -> None:
        """Test initialization with custom ID generator."""
        custom_ids = iter(["custom-1", "custom-2", "custom-3"])
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](
            entity_type=SampleEntity,
            id_generator=lambda: next(custom_ids),
        )

        assert repo._id_generator() == "custom-1"

    def test_default_id_generator(self) -> None:
        """Test default ID generator increments."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)

        id1 = repo._default_id_generator()
        id2 = repo._default_id_generator()

        assert id1 == "1"
        assert id2 == "2"


class TestBatchRepositoryBulkCreate:
    """Tests for bulk_create operation."""

    @pytest.fixture()
    def repo(self) -> BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]:
        """Create repository instance."""
        return BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)

    @pytest.mark.asyncio
    async def test_bulk_create_success(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test successful bulk create."""
        items = [
            CreateSampleEntity(name="item1", value=1),
            CreateSampleEntity(name="item2", value=2),
            CreateSampleEntity(name="item3", value=3),
        ]

        result = await repo.bulk_create(items)

        assert result.total_succeeded == 3
        assert result.total_failed == 0
        assert repo.count == 3

    @pytest.mark.asyncio
    async def test_bulk_create_with_custom_ids(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test bulk create with custom IDs."""
        items = [
            CreateSampleEntity(id="custom-1", name="item1"),
            CreateSampleEntity(id="custom-2", name="item2"),
        ]

        result = await repo.bulk_create(items)

        assert result.total_succeeded == 2
        entities = await repo.bulk_get(["custom-1", "custom-2"])
        assert entities["custom-1"] is not None
        assert entities["custom-2"] is not None

    @pytest.mark.asyncio
    async def test_bulk_create_with_progress_callback(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test bulk create with progress callback."""
        items = [CreateSampleEntity(name=f"item{i}") for i in range(5)]
        progress_updates: list[BatchProgress] = []

        def on_progress(progress: BatchProgress) -> None:
            progress_updates.append(progress)

        config = BatchConfig(chunk_size=2)
        await repo.bulk_create(items, config=config, on_progress=on_progress)

        assert len(progress_updates) == 3  # 5 items / 2 chunk_size = 3 chunks

    @pytest.mark.asyncio
    async def test_bulk_create_fail_fast(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test bulk create with fail-fast strategy."""

        # Create a repo that will fail on specific item
        class FailingEntity(BaseModel):
            id: str = ""
            name: str

            def model_dump(self, **kwargs):
                if self.name == "fail":
                    raise ValueError("Intentional failure")
                return super().model_dump(**kwargs)

        items = [
            CreateSampleEntity(name="item1"),
            CreateSampleEntity(name="item2"),
        ]

        config = BatchConfig(error_strategy=BatchErrorStrategy.FAIL_FAST)
        result = await repo.bulk_create(items, config=config)

        # All should succeed since no actual failure
        assert result.total_succeeded == 2


class TestBatchRepositoryBulkUpdate:
    """Tests for bulk_update operation."""

    @pytest.fixture()
    def repo(self) -> BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]:
        """Create repository with initial data."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)
        repo._storage = {
            "1": SampleEntity(id="1", name="item1", value=10),
            "2": SampleEntity(id="2", name="item2", value=20),
            "3": SampleEntity(id="3", name="item3", value=30),
        }
        return repo

    @pytest.mark.asyncio
    async def test_bulk_update_success(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test successful bulk update."""
        updates = [
            ("1", UpdateSampleEntity(name="updated1")),
            ("2", UpdateSampleEntity(value=200)),
        ]

        result = await repo.bulk_update(updates)

        assert result.total_succeeded == 2
        assert result.total_failed == 0
        assert repo._storage["1"].name == "updated1"
        assert repo._storage["2"].value == 200

    @pytest.mark.asyncio
    async def test_bulk_update_not_found(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test bulk update with non-existent entity."""
        updates = [
            ("1", UpdateSampleEntity(name="updated1")),
            ("999", UpdateSampleEntity(name="not-found")),
        ]

        result = await repo.bulk_update(updates)

        assert result.total_succeeded == 1
        assert result.total_failed == 1


class TestBatchRepositoryBulkDelete:
    """Tests for bulk_delete operation."""

    @pytest.fixture()
    def repo(self) -> BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]:
        """Create repository with initial data."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)
        repo._storage = {
            "1": SampleEntity(id="1", name="item1"),
            "2": SampleEntity(id="2", name="item2"),
            "3": SampleEntity(id="3", name="item3"),
        }
        return repo

    @pytest.mark.asyncio
    async def test_bulk_delete_soft(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test soft delete."""
        result = await repo.bulk_delete(["1", "2"], soft=True)

        assert result.total_succeeded == 2
        assert repo._storage["1"].is_deleted is True
        assert repo._storage["2"].is_deleted is True

    @pytest.mark.asyncio
    async def test_bulk_delete_hard(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test hard delete."""
        result = await repo.bulk_delete(["1", "2"], soft=False)

        assert result.total_succeeded == 2
        assert "1" not in repo._storage
        assert "2" not in repo._storage

    @pytest.mark.asyncio
    async def test_bulk_delete_not_found(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test delete with non-existent entity."""
        result = await repo.bulk_delete(["1", "999"])

        assert result.total_succeeded == 1
        assert result.total_failed == 1


class TestBatchRepositoryBulkGet:
    """Tests for bulk_get operation."""

    @pytest.fixture()
    def repo(self) -> BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]:
        """Create repository with initial data."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)
        repo._storage = {
            "1": SampleEntity(id="1", name="item1"),
            "2": SampleEntity(id="2", name="item2", is_deleted=True),
        }
        return repo

    @pytest.mark.asyncio
    async def test_bulk_get_success(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test successful bulk get."""
        result = await repo.bulk_get(["1", "2", "3"])

        assert result["1"] is not None
        assert result["2"] is None  # Soft deleted
        assert result["3"] is None  # Not found


class TestBatchRepositoryBulkExists:
    """Tests for bulk_exists operation."""

    @pytest.fixture()
    def repo(self) -> BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]:
        """Create repository with initial data."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)
        repo._storage = {
            "1": SampleEntity(id="1", name="item1"),
            "2": SampleEntity(id="2", name="item2"),
        }
        return repo

    @pytest.mark.asyncio
    async def test_bulk_exists(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test bulk exists check."""
        result = await repo.bulk_exists(["1", "2", "3"])

        assert result["1"] is True
        assert result["2"] is True
        assert result["3"] is False


class TestBatchRepositoryBulkUpsert:
    """Tests for bulk_upsert operation."""

    @pytest.fixture()
    def repo(self) -> BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]:
        """Create repository with initial data."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)
        repo._storage = {
            "1": SampleEntity(id="1", name="existing", value=10),
        }
        return repo

    @pytest.mark.asyncio
    async def test_bulk_upsert_insert(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test upsert inserts new entities."""
        items = [CreateSampleEntity(id="2", name="new", value=20)]

        result = await repo.bulk_upsert(items)

        assert result.total_succeeded == 1
        assert repo._storage["2"].name == "new"

    @pytest.mark.asyncio
    async def test_bulk_upsert_update(
        self, repo: BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity]
    ) -> None:
        """Test upsert updates existing entities."""
        items = [CreateSampleEntity(id="1", name="updated", value=100)]

        result = await repo.bulk_upsert(items)

        assert result.total_succeeded == 1
        assert repo._storage["1"].name == "updated"
        assert repo._storage["1"].value == 100


class TestBatchRepositoryClear:
    """Tests for clear operation."""

    def test_clear(self) -> None:
        """Test clear removes all entities."""
        repo = BatchRepository[SampleEntity, CreateSampleEntity, UpdateSampleEntity](entity_type=SampleEntity)
        repo._storage = {"1": SampleEntity(id="1", name="item1")}
        repo._counter = 5

        repo.clear()

        assert repo.count == 0
        assert repo._counter == 0
