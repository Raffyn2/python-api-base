"""Unit tests for token store implementations.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 4.2, 8.2, 8.3, 8.5**
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.auth.token_store.models import StoredToken
from infrastructure.auth.token_store.stores import (
    InMemoryTokenStore,
    RedisTokenStore,
    _validate_token_input,
    get_token_store_sync,
)


class TestValidateTokenInput:
    """Tests for _validate_token_input function."""

    def test_valid_input(self) -> None:
        """Test valid input passes."""
        _validate_token_input(
            jti="token-123",
            user_id="user-456",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    def test_empty_jti_raises(self) -> None:
        """Test empty jti raises ValueError."""
        with pytest.raises(ValueError, match="jti cannot be empty"):
            _validate_token_input(
                jti="",
                user_id="user-456",
                expires_at=datetime.now(UTC),
            )

    def test_whitespace_jti_raises(self) -> None:
        """Test whitespace jti raises ValueError."""
        with pytest.raises(ValueError, match="jti cannot be empty"):
            _validate_token_input(
                jti="   ",
                user_id="user-456",
                expires_at=datetime.now(UTC),
            )

    def test_empty_user_id_raises(self) -> None:
        """Test empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            _validate_token_input(
                jti="token-123",
                user_id="",
                expires_at=datetime.now(UTC),
            )

    def test_naive_datetime_raises(self) -> None:
        """Test naive datetime raises ValueError."""
        with pytest.raises(ValueError, match="timezone-aware"):
            _validate_token_input(
                jti="token-123",
                user_id="user-456",
                expires_at=datetime.now(),  # Naive datetime
            )


class TestInMemoryTokenStore:
    """Tests for InMemoryTokenStore."""

    @pytest.fixture
    def store(self) -> InMemoryTokenStore:
        """Create in-memory token store."""
        return InMemoryTokenStore()

    @pytest.fixture
    def future_time(self) -> datetime:
        """Create future expiration time."""
        return datetime.now(UTC) + timedelta(hours=1)

    @pytest.mark.asyncio
    async def test_store_and_get(
        self, store: InMemoryTokenStore, future_time: datetime
    ) -> None:
        """Test storing and retrieving token."""
        await store.store("jti-1", "user-1", future_time)
        
        token = await store.get("jti-1")
        
        assert token is not None
        assert token.jti == "jti-1"
        assert token.user_id == "user-1"
        assert token.revoked is False

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(
        self, store: InMemoryTokenStore
    ) -> None:
        """Test getting nonexistent token returns None."""
        token = await store.get("nonexistent")
        assert token is None

    @pytest.mark.asyncio
    async def test_revoke_token(
        self, store: InMemoryTokenStore, future_time: datetime
    ) -> None:
        """Test revoking token."""
        await store.store("jti-1", "user-1", future_time)
        
        result = await store.revoke("jti-1")
        
        assert result is True
        token = await store.get("jti-1")
        assert token is not None
        assert token.revoked is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_returns_false(
        self, store: InMemoryTokenStore
    ) -> None:
        """Test revoking nonexistent token returns False."""
        result = await store.revoke("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_for_user(
        self, store: InMemoryTokenStore, future_time: datetime
    ) -> None:
        """Test revoking all tokens for user."""
        await store.store("jti-1", "user-1", future_time)
        await store.store("jti-2", "user-1", future_time)
        await store.store("jti-3", "user-2", future_time)
        
        count = await store.revoke_all_for_user("user-1")
        
        assert count == 2
        assert (await store.get("jti-1")).revoked is True
        assert (await store.get("jti-2")).revoked is True
        assert (await store.get("jti-3")).revoked is False

    @pytest.mark.asyncio
    async def test_is_valid_for_valid_token(
        self, store: InMemoryTokenStore, future_time: datetime
    ) -> None:
        """Test is_valid returns True for valid token."""
        await store.store("jti-1", "user-1", future_time)
        
        assert await store.is_valid("jti-1") is True

    @pytest.mark.asyncio
    async def test_is_valid_for_revoked_token(
        self, store: InMemoryTokenStore, future_time: datetime
    ) -> None:
        """Test is_valid returns False for revoked token."""
        await store.store("jti-1", "user-1", future_time)
        await store.revoke("jti-1")
        
        assert await store.is_valid("jti-1") is False

    @pytest.mark.asyncio
    async def test_is_valid_for_nonexistent_token(
        self, store: InMemoryTokenStore
    ) -> None:
        """Test is_valid returns False for nonexistent token."""
        assert await store.is_valid("nonexistent") is False

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, store: InMemoryTokenStore) -> None:
        """Test cleanup removes expired tokens."""
        past_time = datetime.now(UTC) - timedelta(hours=1)
        future_time = datetime.now(UTC) + timedelta(hours=1)
        
        await store.store("expired-1", "user-1", past_time)
        await store.store("valid-1", "user-1", future_time)
        
        count = await store.cleanup_expired()
        
        assert count == 1
        assert await store.get("expired-1") is None
        assert await store.get("valid-1") is not None

    @pytest.mark.asyncio
    async def test_max_entries_eviction(self) -> None:
        """Test eviction when max entries exceeded."""
        store = InMemoryTokenStore(max_entries=3)
        future_time = datetime.now(UTC) + timedelta(hours=1)
        
        for i in range(5):
            await store.store(f"jti-{i}", "user-1", future_time)
        
        # Should have evicted oldest entries
        assert await store.get("jti-0") is None
        assert await store.get("jti-1") is None
        assert await store.get("jti-4") is not None


class TestRedisTokenStore:
    """Tests for RedisTokenStore."""

    @pytest.fixture
    def mock_redis(self) -> AsyncMock:
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.exists = AsyncMock(return_value=0)
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        redis.sadd = AsyncMock()
        redis.smembers = AsyncMock(return_value=set())
        redis.ttl = AsyncMock(return_value=3600)
        redis.delete = AsyncMock()
        redis.pipeline = MagicMock()
        return redis

    @pytest.fixture
    def store(self, mock_redis: AsyncMock) -> RedisTokenStore:
        """Create Redis token store."""
        return RedisTokenStore(mock_redis)

    @pytest.fixture
    def future_time(self) -> datetime:
        """Create future expiration time."""
        return datetime.now(UTC) + timedelta(hours=1)

    @pytest.mark.asyncio
    async def test_store_token(
        self, store: RedisTokenStore, mock_redis: AsyncMock, future_time: datetime
    ) -> None:
        """Test storing token in Redis."""
        await store.store("jti-1", "user-1", future_time)
        
        mock_redis.setex.assert_called()
        mock_redis.sadd.assert_called()

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(
        self, store: RedisTokenStore
    ) -> None:
        """Test getting nonexistent token returns None."""
        token = await store.get("nonexistent")
        assert token is None

    @pytest.mark.asyncio
    async def test_is_revoked_false(
        self, store: RedisTokenStore, mock_redis: AsyncMock
    ) -> None:
        """Test is_revoked returns False when not revoked."""
        mock_redis.exists.return_value = 0
        
        result = await store.is_revoked("jti-1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_is_revoked_true(
        self, store: RedisTokenStore, mock_redis: AsyncMock
    ) -> None:
        """Test is_revoked returns True when revoked."""
        mock_redis.exists.return_value = 1
        
        result = await store.is_revoked("jti-1")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_add_to_blacklist(
        self, store: RedisTokenStore, mock_redis: AsyncMock
    ) -> None:
        """Test adding token to blacklist."""
        await store.add_to_blacklist("jti-1", 3600)
        
        mock_redis.setex.assert_called_with("revoked:jti-1", 3600, "1")

    @pytest.mark.asyncio
    async def test_cleanup_expired_returns_zero(
        self, store: RedisTokenStore
    ) -> None:
        """Test cleanup returns 0 (Redis handles TTL)."""
        count = await store.cleanup_expired()
        assert count == 0

    @pytest.mark.asyncio
    async def test_is_valid_nonexistent(
        self, store: RedisTokenStore
    ) -> None:
        """Test is_valid returns False for nonexistent token."""
        result = await store.is_valid("nonexistent")
        assert result is False


class TestGetTokenStoreSync:
    """Tests for get_token_store_sync function."""

    def test_returns_in_memory_store(self) -> None:
        """Test returns InMemoryTokenStore."""
        store = get_token_store_sync()
        assert isinstance(store, InMemoryTokenStore)
