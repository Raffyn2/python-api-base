"""Tests for token store implementations.

**Feature: realistic-test-coverage**
**Validates: Requirements 8.2, 8.3, 8.5**
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.auth.token_store.stores import (
    InMemoryTokenStore,
    _validate_token_input,
    get_token_store_sync,
)


class TestValidateTokenInput:
    """Tests for _validate_token_input function."""

    def test_valid_input(self) -> None:
        """Test valid input passes."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        # Should not raise
        _validate_token_input("jti-123", "user-456", expires)

    def test_empty_jti_fails(self) -> None:
        """Test empty jti fails."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        with pytest.raises(ValueError, match="jti"):
            _validate_token_input("", "user-456", expires)

    def test_whitespace_jti_fails(self) -> None:
        """Test whitespace jti fails."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        with pytest.raises(ValueError, match="jti"):
            _validate_token_input("   ", "user-456", expires)

    def test_empty_user_id_fails(self) -> None:
        """Test empty user_id fails."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        with pytest.raises(ValueError, match="user_id"):
            _validate_token_input("jti-123", "", expires)

    def test_naive_datetime_fails(self) -> None:
        """Test naive datetime fails."""
        expires = datetime.now() + timedelta(hours=1)  # No timezone
        with pytest.raises(ValueError, match="timezone"):
            _validate_token_input("jti-123", "user-456", expires)


class TestInMemoryTokenStore:
    """Tests for InMemoryTokenStore."""

    @pytest.mark.asyncio
    async def test_store_and_get(self) -> None:
        """Test storing and retrieving token."""
        store = InMemoryTokenStore()
        expires = datetime.now(UTC) + timedelta(hours=1)
        
        await store.store("jti-123", "user-456", expires)
        token = await store.get("jti-123")
        
        assert token is not None
        assert token.jti == "jti-123"
        assert token.user_id == "user-456"

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        """Test getting non-existent token."""
        store = InMemoryTokenStore()
        token = await store.get("non-existent")
        assert token is None

    @pytest.mark.asyncio
    async def test_revoke(self) -> None:
        """Test revoking token."""
        store = InMemoryTokenStore()
        expires = datetime.now(UTC) + timedelta(hours=1)
        
        await store.store("jti-123", "user-456", expires)
        result = await store.revoke("jti-123")
        
        assert result is True
        token = await store.get("jti-123")
        assert token is not None
        assert token.revoked is True

    @pytest.mark.asyncio
    async def test_revoke_not_found(self) -> None:
        """Test revoking non-existent token."""
        store = InMemoryTokenStore()
        result = await store.revoke("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_for_user(self) -> None:
        """Test revoking all tokens for user."""
        store = InMemoryTokenStore()
        expires = datetime.now(UTC) + timedelta(hours=1)
        
        await store.store("jti-1", "user-456", expires)
        await store.store("jti-2", "user-456", expires)
        await store.store("jti-3", "user-789", expires)
        
        count = await store.revoke_all_for_user("user-456")
        
        assert count == 2
        
        token1 = await store.get("jti-1")
        token2 = await store.get("jti-2")
        token3 = await store.get("jti-3")
        
        assert token1.revoked is True
        assert token2.revoked is True
        assert token3.revoked is False

    @pytest.mark.asyncio
    async def test_is_valid_true(self) -> None:
        """Test is_valid returns True for valid token."""
        store = InMemoryTokenStore()
        expires = datetime.now(UTC) + timedelta(hours=1)
        
        await store.store("jti-123", "user-456", expires)
        result = await store.is_valid("jti-123")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_valid_false_revoked(self) -> None:
        """Test is_valid returns False for revoked token."""
        store = InMemoryTokenStore()
        expires = datetime.now(UTC) + timedelta(hours=1)
        
        await store.store("jti-123", "user-456", expires)
        await store.revoke("jti-123")
        result = await store.is_valid("jti-123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_is_valid_false_not_found(self) -> None:
        """Test is_valid returns False for non-existent token."""
        store = InMemoryTokenStore()
        result = await store.is_valid("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired(self) -> None:
        """Test cleaning up expired tokens."""
        store = InMemoryTokenStore()
        
        # Store expired token
        expired = datetime.now(UTC) - timedelta(hours=1)
        await store.store("jti-expired", "user-456", expired)
        
        # Store valid token
        valid = datetime.now(UTC) + timedelta(hours=1)
        await store.store("jti-valid", "user-456", valid)
        
        count = await store.cleanup_expired()
        
        assert count == 1
        assert await store.get("jti-expired") is None
        assert await store.get("jti-valid") is not None

    @pytest.mark.asyncio
    async def test_max_entries_eviction(self) -> None:
        """Test eviction when max entries exceeded."""
        store = InMemoryTokenStore(max_entries=3)
        expires = datetime.now(UTC) + timedelta(hours=1)
        
        for i in range(5):
            await store.store(f"jti-{i}", "user-456", expires)
        
        # Should have evicted oldest entries
        assert len(store._tokens) <= 3


class TestGetTokenStoreSync:
    """Tests for get_token_store_sync function."""

    def test_returns_in_memory_store(self) -> None:
        """Test returns InMemoryTokenStore."""
        store = get_token_store_sync()
        assert isinstance(store, InMemoryTokenStore)
