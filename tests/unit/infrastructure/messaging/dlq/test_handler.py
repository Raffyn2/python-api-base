"""Tests for DLQ handler module.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.6**
"""

import pytest

from infrastructure.messaging.dlq.handler import DLQEntry, DLQHandler


class TestDLQEntry:
    """Tests for DLQEntry dataclass."""

    def test_create_entry(self) -> None:
        """Test creating a DLQ entry."""
        entry = DLQEntry(
            original_queue="orders",
            message_id="msg-123",
            payload={"order_id": "456"},
            error_message="Processing failed",
            retry_count=3,
        )
        assert entry.original_queue == "orders"
        assert entry.message_id == "msg-123"
        assert entry.payload == {"order_id": "456"}
        assert entry.error_message == "Processing failed"
        assert entry.retry_count == 3

    def test_auto_generated_id(self) -> None:
        """Test auto-generated ID."""
        entry1 = DLQEntry()
        entry2 = DLQEntry()
        assert entry1.id != entry2.id
        assert len(entry1.id) == 36  # UUID format

    def test_default_values(self) -> None:
        """Test default values."""
        entry = DLQEntry()
        assert entry.original_queue == ""
        assert entry.message_id == ""
        assert entry.payload == {}
        assert entry.error_message == ""
        assert entry.retry_count == 0

    def test_to_dict(self) -> None:
        """Test converting entry to dictionary."""
        entry = DLQEntry(
            original_queue="orders",
            message_id="msg-123",
            payload={"order_id": "456"},
            error_message="Processing failed",
            retry_count=3,
        )
        result = entry.to_dict()
        
        assert result["original_queue"] == "orders"
        assert result["message_id"] == "msg-123"
        assert result["payload"] == {"order_id": "456"}
        assert result["error_message"] == "Processing failed"
        assert result["retry_count"] == 3
        assert "created_at" in result
        assert "id" in result


class TestDLQHandler:
    """Tests for DLQHandler."""

    @pytest.mark.asyncio
    async def test_add_entry(self) -> None:
        """Test adding entry to DLQ."""
        handler = DLQHandler()
        entry = DLQEntry(
            original_queue="orders",
            message_id="msg-123",
            error_message="Failed",
        )
        await handler.add(entry)
        
        count = await handler.count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        """Test getting all entries."""
        handler = DLQHandler()
        
        for i in range(3):
            entry = DLQEntry(
                original_queue="orders",
                message_id=f"msg-{i}",
            )
            await handler.add(entry)
        
        entries = await handler.get_all()
        assert len(entries) == 3

    @pytest.mark.asyncio
    async def test_get_all_with_limit(self) -> None:
        """Test getting entries with limit."""
        handler = DLQHandler()
        
        for i in range(10):
            entry = DLQEntry(
                original_queue="orders",
                message_id=f"msg-{i}",
            )
            await handler.add(entry)
        
        entries = await handler.get_all(limit=5)
        assert len(entries) == 5

    @pytest.mark.asyncio
    async def test_retry(self) -> None:
        """Test retrying an entry."""
        handler = DLQHandler()
        entry = DLQEntry(
            original_queue="orders",
            message_id="msg-123",
        )
        await handler.add(entry)
        
        result = await handler.retry(entry.id)
        
        assert result is not None
        assert result.id == entry.id
        
        # Entry should be removed from DLQ
        count = await handler.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_retry_not_found(self) -> None:
        """Test retrying non-existent entry."""
        handler = DLQHandler()
        result = await handler.retry("non-existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Test deleting an entry."""
        handler = DLQHandler()
        entry = DLQEntry(
            original_queue="orders",
            message_id="msg-123",
        )
        await handler.add(entry)
        
        result = await handler.delete(entry.id)
        
        assert result is True
        count = await handler.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test deleting non-existent entry."""
        handler = DLQHandler()
        result = await handler.delete("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_count_empty(self) -> None:
        """Test counting empty DLQ."""
        handler = DLQHandler()
        count = await handler.count()
        assert count == 0
