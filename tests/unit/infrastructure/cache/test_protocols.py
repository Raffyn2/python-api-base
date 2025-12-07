"""Unit tests for cache protocols.

Tests JsonSerializer, CacheKey, and CacheEntry from protocols module.
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.cache.core.protocols import (
    CacheEntry,
    CacheKey,
    JsonSerializer,
    Serializer,
)


class TestJsonSerializer:
    """Tests for JsonSerializer."""

    def test_serialize_string(self) -> None:
        """Test serializing a string."""
        serializer = JsonSerializer[str]()
        
        result = serializer.serialize("test")
        
        assert result == b'"test"'

    def test_deserialize_string(self) -> None:
        """Test deserializing a string."""
        serializer = JsonSerializer[str]()
        
        result = serializer.deserialize(b'"test"')
        
        assert result == "test"

    def test_serialize_dict(self) -> None:
        """Test serializing a dictionary."""
        serializer = JsonSerializer[dict]()
        
        result = serializer.serialize({"key": "value", "num": 42})
        
        assert b'"key"' in result
        assert b'"value"' in result
        assert b'42' in result

    def test_deserialize_dict(self) -> None:
        """Test deserializing a dictionary."""
        serializer = JsonSerializer[dict]()
        
        result = serializer.deserialize(b'{"key": "value", "num": 42}')
        
        assert result == {"key": "value", "num": 42}

    def test_serialize_list(self) -> None:
        """Test serializing a list."""
        serializer = JsonSerializer[list]()
        
        result = serializer.serialize([1, 2, 3])
        
        assert result == b'[1, 2, 3]'

    def test_deserialize_list(self) -> None:
        """Test deserializing a list."""
        serializer = JsonSerializer[list]()
        
        result = serializer.deserialize(b'[1, 2, 3]')
        
        assert result == [1, 2, 3]

    def test_serialize_none(self) -> None:
        """Test serializing None."""
        serializer = JsonSerializer[None]()
        
        result = serializer.serialize(None)
        
        assert result == b'null'

    def test_deserialize_none(self) -> None:
        """Test deserializing None."""
        serializer = JsonSerializer[None]()
        
        result = serializer.deserialize(b'null')
        
        assert result is None

    def test_serialize_nested(self) -> None:
        """Test serializing nested structures."""
        serializer = JsonSerializer[dict]()
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            "count": 2,
        }
        
        result = serializer.serialize(data)
        deserialized = serializer.deserialize(result)
        
        assert deserialized == data

    def test_round_trip(self) -> None:
        """Test serialize then deserialize returns original."""
        serializer = JsonSerializer[dict]()
        original = {"key": "value", "nested": {"a": 1}}
        
        serialized = serializer.serialize(original)
        result = serializer.deserialize(serialized)
        
        assert result == original

    def test_implements_protocol(self) -> None:
        """Test JsonSerializer implements Serializer protocol."""
        serializer = JsonSerializer[str]()
        
        assert isinstance(serializer, Serializer)


class TestCacheKeyProtocols:
    """Tests for CacheKey in protocols module."""

    def test_creation(self) -> None:
        """Test CacheKey creation."""
        key = CacheKey[str](pattern="user:{user_id}")
        
        assert key.pattern == "user:{user_id}"

    def test_format_single_value(self) -> None:
        """Test formatting with single value."""
        key = CacheKey[str](pattern="user:{id}")
        
        result = key.format(id="123")
        
        assert result == "user:123"

    def test_format_multiple_values(self) -> None:
        """Test formatting with multiple values."""
        key = CacheKey[dict](pattern="{prefix}:{type}:{id}")
        
        result = key.format(prefix="app", type="user", id="456")
        
        assert result == "app:user:456"

    def test_str_representation(self) -> None:
        """Test string representation."""
        key = CacheKey[str](pattern="test:pattern")
        
        assert str(key) == "test:pattern"

    def test_immutability(self) -> None:
        """Test CacheKey is immutable."""
        key = CacheKey[str](pattern="test")
        
        with pytest.raises(AttributeError):
            key.pattern = "new"  # type: ignore


class TestCacheEntryProtocols:
    """Tests for CacheEntry in protocols module."""

    def test_creation_minimal(self) -> None:
        """Test minimal CacheEntry creation."""
        now = datetime.now(UTC)
        entry = CacheEntry[str](
            key="test:key",
            value="test_value",
            created_at=now,
        )
        
        assert entry.key == "test:key"
        assert entry.value == "test_value"
        assert entry.created_at == now
        assert entry.ttl is None
        assert entry.expires_at is None
        assert entry.tags == ()

    def test_creation_full(self) -> None:
        """Test full CacheEntry creation."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        
        entry = CacheEntry[dict](
            key="user:123",
            value={"name": "test"},
            created_at=now,
            ttl=3600,
            expires_at=expires,
            tags=("user", "profile"),
        )
        
        assert entry.key == "user:123"
        assert entry.value == {"name": "test"}
        assert entry.ttl == 3600
        assert entry.expires_at == expires
        assert entry.tags == ("user", "profile")

    def test_is_expired_no_expiration(self) -> None:
        """Test is_expired with no expiration."""
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=datetime.now(UTC),
        )
        
        assert entry.is_expired is False

    def test_is_expired_future(self) -> None:
        """Test is_expired with future expiration."""
        now = datetime.now(UTC)
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
        
        assert entry.is_expired is False

    def test_is_expired_past(self) -> None:
        """Test is_expired with past expiration."""
        now = datetime.now(UTC)
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        
        assert entry.is_expired is True

    def test_immutability(self) -> None:
        """Test CacheEntry is immutable."""
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=datetime.now(UTC),
        )
        
        with pytest.raises(AttributeError):
            entry.value = "new"  # type: ignore
