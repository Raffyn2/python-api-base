"""Tests for saga context module.

**Feature: realistic-test-coverage**
**Validates: Requirements 3.2**
"""

import pytest

from infrastructure.db.saga.context import SagaContext


class TestSagaContext:
    """Tests for SagaContext."""

    def test_create_context(self) -> None:
        """Test creating saga context."""
        ctx = SagaContext(saga_id="saga-123")
        assert ctx.saga_id == "saga-123"
        assert ctx.data == {}

    def test_create_with_data(self) -> None:
        """Test creating context with initial data."""
        ctx = SagaContext(
            saga_id="saga-123",
            data={"order_id": "order-456"},
        )
        assert ctx.data["order_id"] == "order-456"

    def test_set_and_get(self) -> None:
        """Test setting and getting values."""
        ctx = SagaContext(saga_id="saga-123")
        ctx.set("result", {"status": "ok"})
        
        result = ctx.get("result")
        assert result == {"status": "ok"}

    def test_get_default(self) -> None:
        """Test get with default value."""
        ctx = SagaContext(saga_id="saga-123")
        result = ctx.get("missing", "default")
        assert result == "default"

    def test_get_none_default(self) -> None:
        """Test get returns None by default."""
        ctx = SagaContext(saga_id="saga-123")
        result = ctx.get("missing")
        assert result is None

    def test_has_existing_key(self) -> None:
        """Test has returns True for existing key."""
        ctx = SagaContext(saga_id="saga-123")
        ctx.set("key", "value")
        assert ctx.has("key") is True

    def test_has_missing_key(self) -> None:
        """Test has returns False for missing key."""
        ctx = SagaContext(saga_id="saga-123")
        assert ctx.has("missing") is False

    def test_clear_results(self) -> None:
        """Test clearing results."""
        ctx = SagaContext(saga_id="saga-123")
        ctx.set("key1", "value1")
        ctx.set("key2", "value2")
        
        ctx.clear_results()
        
        assert ctx.has("key1") is False
        assert ctx.has("key2") is False

    def test_data_separate_from_results(self) -> None:
        """Test data is separate from results."""
        ctx = SagaContext(
            saga_id="saga-123",
            data={"initial": "data"},
        )
        ctx.set("result", "value")
        
        # Data should be unchanged
        assert ctx.data == {"initial": "data"}
        # Result should be accessible
        assert ctx.get("result") == "value"

    def test_overwrite_value(self) -> None:
        """Test overwriting existing value."""
        ctx = SagaContext(saga_id="saga-123")
        ctx.set("key", "value1")
        ctx.set("key", "value2")
        
        assert ctx.get("key") == "value2"
