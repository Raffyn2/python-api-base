"""Unit tests for audit trail with diff tracking.

Tests AuditEntry, DiffCalculator, AuditService, and InMemoryAuditBackend.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.security.audit.trail import (
    AuditAction,
    AuditEntry,
    AuditService,
    DiffCalculator,
    FieldChange,
    InMemoryAuditBackend,
)


@dataclass
class SampleEntity:
    """Sample entity for testing."""

    id: str
    name: str
    value: int


class TestAuditAction:
    """Tests for AuditAction enum."""

    def test_create_value(self) -> None:
        """Test CREATE value."""
        assert AuditAction.CREATE.value == "create"

    def test_update_value(self) -> None:
        """Test UPDATE value."""
        assert AuditAction.UPDATE.value == "update"

    def test_delete_value(self) -> None:
        """Test DELETE value."""
        assert AuditAction.DELETE.value == "delete"

    def test_read_value(self) -> None:
        """Test READ value."""
        assert AuditAction.READ.value == "read"


class TestFieldChange:
    """Tests for FieldChange dataclass."""

    def test_creation(self) -> None:
        """Test FieldChange creation."""
        change = FieldChange(
            field_name="name",
            old_value="old",
            new_value="new",
            field_type="str",
        )

        assert change.field_name == "name"
        assert change.old_value == "old"
        assert change.new_value == "new"
        assert change.field_type == "str"

    def test_default_field_type(self) -> None:
        """Test default field_type."""
        change = FieldChange(
            field_name="name",
            old_value="old",
            new_value="new",
        )

        assert change.field_type == "unknown"


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_creation(self) -> None:
        """Test AuditEntry creation."""
        entry = AuditEntry(
            id="entry-1",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=datetime.now(UTC),
            user_id="admin",
        )

        assert entry.id == "entry-1"
        assert entry.entity_type == "user"
        assert entry.action == AuditAction.CREATE

    def test_checksum_computed(self) -> None:
        """Test checksum is computed on creation."""
        entry = AuditEntry(
            id="entry-1",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=datetime.now(UTC),
            user_id="admin",
        )

        assert entry.checksum != ""
        assert len(entry.checksum) == 16

    def test_checksum_consistent(self) -> None:
        """Test checksum is consistent for same data."""
        entry1 = AuditEntry(
            id="entry-1",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=datetime.now(UTC),
            user_id="admin",
            before_snapshot={"name": "test"},
        )
        entry2 = AuditEntry(
            id="entry-2",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=datetime.now(UTC),
            user_id="admin",
            before_snapshot={"name": "test"},
        )

        assert entry1.checksum == entry2.checksum


class TestDiffCalculator:
    """Tests for DiffCalculator."""

    def test_compute_diff_added_field(self) -> None:
        """Test diff with added field."""
        before = {"name": "test"}
        after = {"name": "test", "value": 42}

        changes = DiffCalculator.compute_diff(before, after)

        assert len(changes) == 1
        assert changes[0].field_name == "value"
        assert changes[0].old_value is None
        assert changes[0].new_value == 42

    def test_compute_diff_removed_field(self) -> None:
        """Test diff with removed field."""
        before = {"name": "test", "value": 42}
        after = {"name": "test"}

        changes = DiffCalculator.compute_diff(before, after)

        assert len(changes) == 1
        assert changes[0].field_name == "value"
        assert changes[0].old_value == 42
        assert changes[0].new_value is None

    def test_compute_diff_changed_field(self) -> None:
        """Test diff with changed field."""
        before = {"name": "old"}
        after = {"name": "new"}

        changes = DiffCalculator.compute_diff(before, after)

        assert len(changes) == 1
        assert changes[0].field_name == "name"
        assert changes[0].old_value == "old"
        assert changes[0].new_value == "new"

    def test_compute_diff_no_changes(self) -> None:
        """Test diff with no changes."""
        before = {"name": "test", "value": 42}
        after = {"name": "test", "value": 42}

        changes = DiffCalculator.compute_diff(before, after)

        assert len(changes) == 0

    def test_compute_diff_from_none(self) -> None:
        """Test diff from None (creation)."""
        after = {"name": "test", "value": 42}

        changes = DiffCalculator.compute_diff(None, after)

        assert len(changes) == 2

    def test_compute_diff_to_none(self) -> None:
        """Test diff to None (deletion)."""
        before = {"name": "test", "value": 42}

        changes = DiffCalculator.compute_diff(before, None)

        assert len(changes) == 2

    def test_apply_diff(self) -> None:
        """Test applying diff to reconstruct state."""
        base = {"name": "old", "value": 42}
        changes = [
            FieldChange(field_name="name", old_value="old", new_value="new"),
            FieldChange(field_name="extra", old_value=None, new_value="added"),
        ]

        result = DiffCalculator.apply_diff(base, changes)

        assert result["name"] == "new"
        assert result["value"] == 42
        assert result["extra"] == "added"

    def test_apply_diff_remove_field(self) -> None:
        """Test applying diff that removes a field."""
        base = {"name": "test", "value": 42}
        changes = [
            FieldChange(field_name="value", old_value=42, new_value=None),
        ]

        result = DiffCalculator.apply_diff(base, changes)

        assert "value" not in result
        assert result["name"] == "test"


class TestInMemoryAuditBackend:
    """Tests for InMemoryAuditBackend."""

    @pytest.fixture
    def backend(self) -> InMemoryAuditBackend:
        """Create backend instance."""
        return InMemoryAuditBackend()

    @pytest.mark.asyncio
    async def test_save_and_find_by_entity(
        self, backend: InMemoryAuditBackend
    ) -> None:
        """Test save and find_by_entity."""
        entry = AuditEntry(
            id="entry-1",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=datetime.now(UTC),
            user_id="admin",
        )

        await backend.save(entry)
        results = await backend.find_by_entity("user", "user-123")

        assert len(results) == 1
        assert results[0].id == "entry-1"

    @pytest.mark.asyncio
    async def test_find_by_user(self, backend: InMemoryAuditBackend) -> None:
        """Test find_by_user."""
        entry = AuditEntry(
            id="entry-1",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=datetime.now(UTC),
            user_id="admin",
        )

        await backend.save(entry)
        results = await backend.find_by_user("admin")

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_find_by_time_range(self, backend: InMemoryAuditBackend) -> None:
        """Test find_by_time_range."""
        now = datetime.now(UTC)
        entry = AuditEntry(
            id="entry-1",
            entity_type="user",
            entity_id="user-123",
            action=AuditAction.CREATE,
            timestamp=now,
            user_id="admin",
        )

        await backend.save(entry)
        results = await backend.find_by_time_range(
            now - timedelta(hours=1), now + timedelta(hours=1)
        )

        assert len(results) == 1


class TestAuditService:
    """Tests for AuditService."""

    @pytest.fixture
    def service(self) -> AuditService[SampleEntity]:
        """Create service instance."""
        backend = InMemoryAuditBackend()
        return AuditService[SampleEntity](backend)

    @pytest.mark.asyncio
    async def test_log_create(self, service: AuditService[SampleEntity]) -> None:
        """Test log_create."""
        entity = SampleEntity(id="1", name="test", value=42)

        entry = await service.log_create(
            entity_type="sample",
            entity_id="1",
            entity=entity,
            user_id="admin",
        )

        assert entry.action == AuditAction.CREATE
        assert entry.after_snapshot is not None
        assert entry.after_snapshot["name"] == "test"

    @pytest.mark.asyncio
    async def test_log_update(self, service: AuditService[SampleEntity]) -> None:
        """Test log_update."""
        before = SampleEntity(id="1", name="old", value=42)
        after = SampleEntity(id="1", name="new", value=42)

        entry = await service.log_update(
            entity_type="sample",
            entity_id="1",
            before=before,
            after=after,
            user_id="admin",
        )

        assert entry.action == AuditAction.UPDATE
        assert len(entry.changes) == 1
        assert entry.changes[0].field_name == "name"

    @pytest.mark.asyncio
    async def test_log_delete(self, service: AuditService[SampleEntity]) -> None:
        """Test log_delete."""
        entity = SampleEntity(id="1", name="test", value=42)

        entry = await service.log_delete(
            entity_type="sample",
            entity_id="1",
            entity=entity,
            user_id="admin",
        )

        assert entry.action == AuditAction.DELETE
        assert entry.before_snapshot is not None
        assert entry.after_snapshot is None

    @pytest.mark.asyncio
    async def test_get_history(self, service: AuditService[SampleEntity]) -> None:
        """Test get_history."""
        entity = SampleEntity(id="1", name="test", value=42)
        await service.log_create(
            entity_type="sample", entity_id="1", entity=entity
        )

        history = await service.get_history("sample", "1")

        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_reconstruct_at(self, service: AuditService[SampleEntity]) -> None:
        """Test reconstruct_at."""
        entity1 = SampleEntity(id="1", name="v1", value=1)
        entity2 = SampleEntity(id="1", name="v2", value=2)

        await service.log_create(
            entity_type="sample", entity_id="1", entity=entity1
        )
        await service.log_update(
            entity_type="sample", entity_id="1", before=entity1, after=entity2
        )

        state = await service.reconstruct_at(
            "sample", "1", datetime.now(UTC) + timedelta(hours=1)
        )

        assert state is not None
        assert state["name"] == "v2"
