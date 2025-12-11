"""Tests for inbox pattern module.

**Feature: realistic-test-coverage**
**Validates: Requirements 9.5**
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.messaging.inbox import (
    InboxEntry,
    InboxService,
    InboxStatus,
    InMemoryInboxRepository,
    MockMessageHandler,
)


class TestInboxStatus:
    """Tests for InboxStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING status value."""
        assert InboxStatus.PENDING.value == "pending"

    def test_processing_value(self) -> None:
        """Test PROCESSING status value."""
        assert InboxStatus.PROCESSING.value == "processing"

    def test_processed_value(self) -> None:
        """Test PROCESSED status value."""
        assert InboxStatus.PROCESSED.value == "processed"

    def test_failed_value(self) -> None:
        """Test FAILED status value."""
        assert InboxStatus.FAILED.value == "failed"


class TestInboxEntry:
    """Tests for InboxEntry dataclass."""

    def test_create_entry(self) -> None:
        """Test creating inbox entry."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
        )
        assert entry.message_id == "msg-1"
        assert entry.message_type == "OrderCreated"
        assert entry.payload == {"order_id": "123"}
        assert entry.status == InboxStatus.PENDING
        assert entry.idempotency_key is not None

    def test_create_with_custom_idempotency_key(self) -> None:
        """Test creating entry with custom idempotency key."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
            idempotency_key="custom-key",
        )
        assert entry.idempotency_key == "custom-key"

    def test_generate_idempotency_key_deterministic(self) -> None:
        """Test idempotency key generation is deterministic."""
        key1 = InboxEntry._generate_idempotency_key("msg-1", "OrderCreated", {"order_id": "123"})
        key2 = InboxEntry._generate_idempotency_key("msg-1", "OrderCreated", {"order_id": "123"})
        assert key1 == key2

    def test_generate_idempotency_key_different_for_different_content(self) -> None:
        """Test idempotency key differs for different content."""
        key1 = InboxEntry._generate_idempotency_key("msg-1", "OrderCreated", {"order_id": "123"})
        key2 = InboxEntry._generate_idempotency_key("msg-2", "OrderCreated", {"order_id": "123"})
        assert key1 != key2

    def test_mark_processing(self) -> None:
        """Test marking entry as processing."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processing()
        assert entry.status == InboxStatus.PROCESSING

    def test_mark_processed(self) -> None:
        """Test marking entry as processed."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processed()
        assert entry.status == InboxStatus.PROCESSED
        assert entry.processed_at is not None

    def test_mark_failed(self) -> None:
        """Test marking entry as failed."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_failed("Processing error")
        assert entry.status == InboxStatus.FAILED
        assert entry.error_message == "Processing error"

    def test_to_dict(self) -> None:
        """Test converting entry to dictionary."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
        )
        result = entry.to_dict()
        assert result["message_id"] == "msg-1"
        assert result["message_type"] == "OrderCreated"
        assert result["payload"] == {"order_id": "123"}
        assert result["status"] == "pending"

    def test_to_dict_with_processed_at(self) -> None:
        """Test to_dict includes processed_at when set."""
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processed()
        result = entry.to_dict()
        assert result["processed_at"] is not None


class TestInMemoryInboxRepository:
    """Tests for InMemoryInboxRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self) -> None:
        """Test saving and retrieving entry by ID."""
        repo = InMemoryInboxRepository()
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        await repo.save(entry)
        result = await repo.get_by_id("msg-1")
        assert result is not None
        assert result.message_id == "msg-1"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test getting non-existent entry."""
        repo = InMemoryInboxRepository()
        result = await repo.get_by_id("non-existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_idempotency_key(self) -> None:
        """Test retrieving entry by idempotency key."""
        repo = InMemoryInboxRepository()
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
            idempotency_key="custom-key",
        )
        await repo.save(entry)
        result = await repo.get_by_idempotency_key("custom-key")
        assert result is not None
        assert result.message_id == "msg-1"

    @pytest.mark.asyncio
    async def test_get_by_idempotency_key_not_found(self) -> None:
        """Test getting entry by non-existent idempotency key."""
        repo = InMemoryInboxRepository()
        result = await repo.get_by_idempotency_key("non-existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self) -> None:
        """Test updating entry."""
        repo = InMemoryInboxRepository()
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        await repo.save(entry)
        entry.mark_processed()
        await repo.update(entry)
        result = await repo.get_by_id("msg-1")
        assert result is not None
        assert result.status == InboxStatus.PROCESSED

    @pytest.mark.asyncio
    async def test_delete_processed(self) -> None:
        """Test deleting processed entries."""
        repo = InMemoryInboxRepository()

        # Create and process an entry
        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processed()
        entry.processed_at = datetime.now(UTC) - timedelta(days=2)
        await repo.save(entry)

        # Delete entries older than 1 day
        deleted = await repo.delete_processed(datetime.now(UTC) - timedelta(days=1))
        assert deleted == 1
        assert await repo.get_by_id("msg-1") is None

    @pytest.mark.asyncio
    async def test_delete_processed_keeps_recent(self) -> None:
        """Test delete_processed keeps recent entries."""
        repo = InMemoryInboxRepository()

        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processed()
        await repo.save(entry)

        # Try to delete entries older than 1 day (entry is recent)
        deleted = await repo.delete_processed(datetime.now(UTC) - timedelta(days=1))
        assert deleted == 0
        assert await repo.get_by_id("msg-1") is not None

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        """Test counting entries."""
        repo = InMemoryInboxRepository()
        assert repo.count() == 0

        for i in range(3):
            entry = InboxEntry.create(
                message_id=f"msg-{i}",
                message_type="OrderCreated",
                payload={},
            )
            await repo.save(entry)

        assert repo.count() == 3


class TestMockMessageHandler:
    """Tests for MockMessageHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful message handling."""
        handler = MockMessageHandler()
        await handler.handle("OrderCreated", {"order_id": "123"})
        assert len(handler.handled_messages) == 1
        assert handler.handled_messages[0] == ("OrderCreated", {"order_id": "123"})

    @pytest.mark.asyncio
    async def test_handle_failure(self) -> None:
        """Test failed message handling."""
        handler = MockMessageHandler(should_fail=True)
        with pytest.raises(Exception):
            await handler.handle("OrderCreated", {})

    def test_clear(self) -> None:
        """Test clearing handled messages."""
        handler = MockMessageHandler()
        handler._handled.append(("test", {}))
        handler.clear()
        assert len(handler.handled_messages) == 0


class TestInboxService:
    """Tests for InboxService."""

    @pytest.mark.asyncio
    async def test_receive_new_message(self) -> None:
        """Test receiving a new message."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        is_new, entry = await service.receive(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
        )

        assert is_new is True
        assert entry.message_id == "msg-1"

    @pytest.mark.asyncio
    async def test_receive_duplicate_message(self) -> None:
        """Test receiving a duplicate message with same idempotency key."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        await service.receive(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
            idempotency_key="shared-key",
        )

        is_new, _entry = await service.receive(
            message_id="msg-2",
            message_type="OrderCreated",
            payload={"order_id": "456"},
            idempotency_key="shared-key",
        )

        # Same idempotency key means duplicate
        assert is_new is False

    @pytest.mark.asyncio
    async def test_process_success(self) -> None:
        """Test successful message processing."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        _, entry = await service.receive(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
        )

        success = await service.process(entry)

        assert success is True
        assert len(handler.handled_messages) == 1

    @pytest.mark.asyncio
    async def test_process_failure(self) -> None:
        """Test failed message processing."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler(should_fail=True)
        service = InboxService(repo, handler)

        _, entry = await service.receive(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )

        success = await service.process(entry)

        assert success is False
        updated = await repo.get_by_id("msg-1")
        assert updated is not None
        assert updated.status == InboxStatus.FAILED

    @pytest.mark.asyncio
    async def test_process_already_processed(self) -> None:
        """Test processing already processed entry."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        _, entry = await service.receive(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processed()
        await repo.update(entry)

        success = await service.process(entry)

        assert success is True
        assert len(handler.handled_messages) == 0  # Not processed again

    @pytest.mark.asyncio
    async def test_receive_and_process(self) -> None:
        """Test receive and process in one call."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        is_new, success = await service.receive_and_process(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
        )

        assert is_new is True
        assert success is True

    @pytest.mark.asyncio
    async def test_receive_and_process_duplicate(self) -> None:
        """Test receive_and_process with duplicate idempotency key."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        await service.receive_and_process(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={"order_id": "123"},
            idempotency_key="shared-key",
        )

        is_new, success = await service.receive_and_process(
            message_id="msg-2",
            message_type="OrderCreated",
            payload={"order_id": "456"},
            idempotency_key="shared-key",
        )

        assert is_new is False
        assert success is True  # Original was processed

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        """Test cleanup of old entries."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        _, entry = await service.receive(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
        )
        entry.mark_processed()
        entry.processed_at = datetime.now(UTC) - timedelta(days=10)
        await repo.update(entry)

        deleted = await service.cleanup(datetime.now(UTC) - timedelta(days=7))
        assert deleted == 1

    @pytest.mark.asyncio
    async def test_is_duplicate(self) -> None:
        """Test duplicate detection."""
        repo = InMemoryInboxRepository()
        handler = MockMessageHandler()
        service = InboxService(repo, handler)

        entry = InboxEntry.create(
            message_id="msg-1",
            message_type="OrderCreated",
            payload={},
            idempotency_key="test-key",
        )
        await repo.save(entry)

        assert await service.is_duplicate("test-key") is True
        assert await service.is_duplicate("other-key") is False
