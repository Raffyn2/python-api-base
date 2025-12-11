"""Unit tests for soft delete functionality.

Tests SoftDeleteConfig, DeletedRecord, InMemorySoftDeleteBackend, and SoftDeleteService.
"""

from datetime import UTC, datetime

import pytest

from infrastructure.db.models.soft_delete import (
    DeletedRecord,
    InMemorySoftDeleteBackend,
    SoftDeleteConfig,
    SoftDeleteService,
)


class TestSoftDeleteConfig:
    """Tests for SoftDeleteConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = SoftDeleteConfig()

        assert config.cascade_relations == []
        assert config.restore_cascade is True
        assert config.permanent_delete_after_days is None
        assert config.track_deleted_by is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = SoftDeleteConfig(
            cascade_relations=["items", "comments"],
            restore_cascade=False,
            permanent_delete_after_days=30,
            track_deleted_by=False,
        )

        assert config.cascade_relations == ["items", "comments"]
        assert config.restore_cascade is False
        assert config.permanent_delete_after_days == 30
        assert config.track_deleted_by is False


class TestDeletedRecord:
    """Tests for DeletedRecord dataclass."""

    def test_creation(self) -> None:
        """Test DeletedRecord creation."""
        now = datetime.now(UTC)

        record = DeletedRecord[dict](
            id="record-123",
            entity_type="User",
            original_id="user-456",
            data={"name": "Test"},
            deleted_at=now,
        )

        assert record.id == "record-123"
        assert record.entity_type == "User"
        assert record.original_id == "user-456"
        assert record.data == {"name": "Test"}
        assert record.deleted_at == now
        assert record.deleted_by is None
        assert record.cascade_deleted == []
        assert record.restore_token == ""

    def test_creation_with_all_fields(self) -> None:
        """Test DeletedRecord with all fields."""
        now = datetime.now(UTC)

        record = DeletedRecord[str](
            id="record-123",
            entity_type="Order",
            original_id="order-789",
            data="order data",
            deleted_at=now,
            deleted_by="admin",
            cascade_deleted=["item-1", "item-2"],
            restore_token="token-abc",
        )

        assert record.deleted_by == "admin"
        assert record.cascade_deleted == ["item-1", "item-2"]
        assert record.restore_token == "token-abc"


class TestInMemorySoftDeleteBackend:
    """Tests for InMemorySoftDeleteBackend."""

    @pytest.fixture()
    def backend(self) -> InMemorySoftDeleteBackend[dict]:
        """Create a fresh backend for each test."""
        return InMemorySoftDeleteBackend[dict]()

    @pytest.mark.asyncio
    async def test_mark_deleted(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test marking an entity as deleted."""
        await backend.mark_deleted("User", "user-123", "admin")

        assert await backend.is_deleted("User", "user-123") is True

    @pytest.mark.asyncio
    async def test_is_deleted_not_deleted(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test is_deleted returns False for non-deleted entity."""
        assert await backend.is_deleted("User", "user-123") is False

    @pytest.mark.asyncio
    async def test_restore(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test restoring a deleted entity."""
        await backend.mark_deleted("User", "user-123", None)

        result = await backend.restore("User", "user-123")

        assert result is True
        assert await backend.is_deleted("User", "user-123") is False

    @pytest.mark.asyncio
    async def test_restore_not_deleted(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test restoring a non-deleted entity returns False."""
        result = await backend.restore("User", "user-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_deleted(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test getting all deleted records of a type."""
        await backend.mark_deleted("User", "user-1", None)
        await backend.mark_deleted("User", "user-2", None)
        await backend.mark_deleted("Order", "order-1", None)

        users = await backend.get_deleted("User")
        orders = await backend.get_deleted("Order")

        assert len(users) == 2
        assert len(orders) == 1

    @pytest.mark.asyncio
    async def test_permanent_delete(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test permanently deleting an entity."""
        await backend.mark_deleted("User", "user-123", None)

        result = await backend.permanent_delete("User", "user-123")

        assert result is True
        assert await backend.is_deleted("User", "user-123") is False

    @pytest.mark.asyncio
    async def test_permanent_delete_not_deleted(self, backend: InMemorySoftDeleteBackend[dict]) -> None:
        """Test permanent delete on non-deleted entity returns False."""
        result = await backend.permanent_delete("User", "user-123")

        assert result is False


class TestSoftDeleteService:
    """Tests for SoftDeleteService."""

    @pytest.fixture()
    def backend(self) -> InMemorySoftDeleteBackend[dict]:
        """Create a fresh backend."""
        return InMemorySoftDeleteBackend[dict]()

    @pytest.fixture()
    def service(self, backend: InMemorySoftDeleteBackend[dict]) -> SoftDeleteService[dict]:
        """Create a service with the backend."""
        return SoftDeleteService[dict](backend)

    @pytest.mark.asyncio
    async def test_delete(self, service: SoftDeleteService[dict]) -> None:
        """Test deleting an entity."""
        result = await service.delete("User", "user-123", "admin")

        assert result == [("User", "user-123")]
        assert await service.is_deleted("User", "user-123") is True

    @pytest.mark.asyncio
    async def test_restore(self, service: SoftDeleteService[dict]) -> None:
        """Test restoring a deleted entity."""
        await service.delete("User", "user-123", None)

        result = await service.restore("User", "user-123")

        assert result == [("User", "user-123")]
        assert await service.is_deleted("User", "user-123") is False

    @pytest.mark.asyncio
    async def test_is_deleted(self, service: SoftDeleteService[dict]) -> None:
        """Test checking if entity is deleted."""
        assert await service.is_deleted("User", "user-123") is False

        await service.delete("User", "user-123", None)

        assert await service.is_deleted("User", "user-123") is True

    @pytest.mark.asyncio
    async def test_get_deleted_records(self, service: SoftDeleteService[dict]) -> None:
        """Test getting deleted records."""
        await service.delete("User", "user-1", None)
        await service.delete("User", "user-2", None)

        records = await service.get_deleted_records("User")

        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_permanent_delete(self, service: SoftDeleteService[dict]) -> None:
        """Test permanent deletion."""
        await service.delete("User", "user-123", None)

        result = await service.permanent_delete("User", "user-123")

        assert result is True
        assert await service.is_deleted("User", "user-123") is False

    @pytest.mark.asyncio
    async def test_configure(self, service: SoftDeleteService[dict]) -> None:
        """Test configuring soft delete for entity type."""
        config = SoftDeleteConfig(
            cascade_relations=["items"],
            permanent_delete_after_days=30,
        )

        service.configure("Order", config)

        # Configuration should be stored (no direct way to verify, but no error)
        await service.delete("Order", "order-123", None)
        assert await service.is_deleted("Order", "order-123") is True

    @pytest.mark.asyncio
    async def test_hooks(self, service: SoftDeleteService[dict]) -> None:
        """Test delete/restore hooks."""
        hook_calls: list[tuple[str, str, str]] = []

        async def before_delete_hook(entity_type: str, entity_id: str) -> None:
            hook_calls.append(("before_delete", entity_type, entity_id))

        async def after_delete_hook(entity_type: str, entity_id: str) -> None:
            hook_calls.append(("after_delete", entity_type, entity_id))

        service.register_hook("before_delete", before_delete_hook)
        service.register_hook("after_delete", after_delete_hook)

        await service.delete("User", "user-123", None)

        assert ("before_delete", "User", "user-123") in hook_calls
        assert ("after_delete", "User", "user-123") in hook_calls

    @pytest.mark.asyncio
    async def test_cleanup_expired_no_config(self, service: SoftDeleteService[dict]) -> None:
        """Test cleanup with no retention config returns 0."""
        await service.delete("User", "user-123", None)

        count = await service.cleanup_expired("User")

        assert count == 0
