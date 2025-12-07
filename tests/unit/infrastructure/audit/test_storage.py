"""Tests for audit storage module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from datetime import datetime, timedelta

import pytest

from infrastructure.audit.storage import AuditStore, InMemoryAuditStore
from infrastructure.audit.trail import AuditAction, AuditRecord


class TestInMemoryAuditStore:
    """Tests for InMemoryAuditStore."""

    @pytest.fixture
    def store(self) -> InMemoryAuditStore:
        """Create a fresh store for each test."""
        return InMemoryAuditStore()

    @pytest.fixture
    def sample_record(self) -> AuditRecord[dict]:
        """Create a sample audit record."""
        return AuditRecord(
            id="record-001",
            entity_type="User",
            entity_id="user-123",
            action=AuditAction.CREATE,
            user_id="admin-001",
            correlation_id="corr-001",
            timestamp=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_save_returns_record_id(
        self, store: InMemoryAuditStore, sample_record: AuditRecord
    ) -> None:
        """Test that save returns the record ID."""
        result = await store.save(sample_record)
        assert result == sample_record.id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_saved_record(
        self, store: InMemoryAuditStore, sample_record: AuditRecord
    ) -> None:
        """Test retrieving a saved record by ID."""
        await store.save(sample_record)
        result = await store.get_by_id(sample_record.id)
        assert result is not None
        assert result.id == sample_record.id
        assert result.entity_type == sample_record.entity_type

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test that get_by_id returns None for non-existent record."""
        result = await store.get_by_id("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_entity_returns_matching_records(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test retrieving records by entity type and ID."""
        records = [
            AuditRecord(
                id=f"rec-{i}",
                entity_type="User",
                entity_id="user-123",
                action=AuditAction.UPDATE,
                timestamp=datetime.now() - timedelta(hours=i),
            )
            for i in range(3)
        ]
        for record in records:
            await store.save(record)

        # Add a record for different entity
        other_record = AuditRecord(
            id="rec-other",
            entity_type="User",
            entity_id="user-456",
            action=AuditAction.CREATE,
        )
        await store.save(other_record)

        result = await store.get_by_entity("User", "user-123")
        assert len(result) == 3
        assert all(r.entity_id == "user-123" for r in result)

    @pytest.mark.asyncio
    async def test_get_by_entity_respects_limit(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test that get_by_entity respects the limit parameter."""
        for i in range(10):
            record = AuditRecord(
                id=f"rec-{i}",
                entity_type="Order",
                entity_id="order-001",
                action=AuditAction.UPDATE,
                timestamp=datetime.now() - timedelta(minutes=i),
            )
            await store.save(record)

        result = await store.get_by_entity("Order", "order-001", limit=5)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_by_entity_returns_sorted_by_timestamp(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test that records are sorted by timestamp descending."""
        base_time = datetime.now()
        for i in range(3):
            record = AuditRecord(
                id=f"rec-{i}",
                entity_type="Product",
                entity_id="prod-001",
                action=AuditAction.UPDATE,
                timestamp=base_time - timedelta(hours=i),
            )
            await store.save(record)

        result = await store.get_by_entity("Product", "prod-001")
        # Most recent first
        assert result[0].id == "rec-0"
        assert result[2].id == "rec-2"

    @pytest.mark.asyncio
    async def test_get_by_user_returns_matching_records(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test retrieving records by user ID."""
        for i in range(3):
            record = AuditRecord(
                id=f"rec-{i}",
                entity_type="Document",
                entity_id=f"doc-{i}",
                action=AuditAction.READ,
                user_id="user-admin",
                timestamp=datetime.now() - timedelta(minutes=i),
            )
            await store.save(record)

        # Add record for different user
        other_record = AuditRecord(
            id="rec-other",
            entity_type="Document",
            entity_id="doc-99",
            action=AuditAction.READ,
            user_id="user-guest",
        )
        await store.save(other_record)

        result = await store.get_by_user("user-admin")
        assert len(result) == 3
        assert all(r.user_id == "user-admin" for r in result)

    @pytest.mark.asyncio
    async def test_get_by_user_respects_limit(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test that get_by_user respects the limit parameter."""
        for i in range(10):
            record = AuditRecord(
                id=f"rec-{i}",
                entity_type="File",
                entity_id=f"file-{i}",
                action=AuditAction.READ,
                user_id="power-user",
                timestamp=datetime.now() - timedelta(minutes=i),
            )
            await store.save(record)

        result = await store.get_by_user("power-user", limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_by_correlation_returns_matching_records(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test retrieving records by correlation ID."""
        correlation_id = "request-12345"
        for i in range(3):
            record = AuditRecord(
                id=f"rec-{i}",
                entity_type="Transaction",
                entity_id=f"tx-{i}",
                action=AuditAction.CREATE,
                correlation_id=correlation_id,
            )
            await store.save(record)

        # Add record with different correlation
        other_record = AuditRecord(
            id="rec-other",
            entity_type="Transaction",
            entity_id="tx-99",
            action=AuditAction.CREATE,
            correlation_id="other-correlation",
        )
        await store.save(other_record)

        result = await store.get_by_correlation(correlation_id)
        assert len(result) == 3
        assert all(r.correlation_id == correlation_id for r in result)

    @pytest.mark.asyncio
    async def test_get_by_correlation_returns_empty_for_no_match(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test that get_by_correlation returns empty list for no matches."""
        result = await store.get_by_correlation("non-existent-correlation")
        assert result == []

    @pytest.mark.asyncio
    async def test_multiple_saves_same_id_overwrites(
        self, store: InMemoryAuditStore
    ) -> None:
        """Test that saving with same ID overwrites the record."""
        record1 = AuditRecord(
            id="same-id",
            entity_type="User",
            entity_id="user-1",
            action=AuditAction.CREATE,
        )
        record2 = AuditRecord(
            id="same-id",
            entity_type="User",
            entity_id="user-2",
            action=AuditAction.UPDATE,
        )

        await store.save(record1)
        await store.save(record2)

        result = await store.get_by_id("same-id")
        assert result is not None
        assert result.entity_id == "user-2"
        assert result.action == AuditAction.UPDATE


class TestAuditStoreProtocol:
    """Tests for AuditStore protocol."""

    def test_in_memory_store_implements_protocol(self) -> None:
        """Test that InMemoryAuditStore implements AuditStore protocol."""
        store = InMemoryAuditStore()
        assert isinstance(store, AuditStore)

    def test_protocol_is_runtime_checkable(self) -> None:
        """Test that AuditStore protocol is runtime checkable."""
        assert hasattr(AuditStore, "__protocol_attrs__") or hasattr(
            AuditStore, "_is_protocol"
        )
