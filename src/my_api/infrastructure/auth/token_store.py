"""Refresh token storage for JWT authentication.

**Feature: api-base-improvements**
**Validates: Requirements 1.4, 1.5**
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StoredToken:
    """Stored refresh token data.

    Attributes:
        jti: JWT ID (unique token identifier).
        user_id: User who owns the token.
        created_at: When the token was created.
        expires_at: When the token expires.
        revoked: Whether the token has been revoked.
    """

    jti: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    revoked: bool = False

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.revoked and not self.is_expired()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "jti": self.jti,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked": self.revoked,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoredToken":
        """Create from dictionary."""
        return cls(
            jti=data["jti"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            revoked=data.get("revoked", False),
        )


@runtime_checkable
class TokenStoreProtocol(Protocol):
    """Protocol for token storage implementations."""

    async def store(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        """Store a refresh token."""
        ...

    async def get(self, jti: str) -> StoredToken | None:
        """Get a stored token by JTI."""
        ...

    async def revoke(self, jti: str) -> bool:
        """Revoke a token by JTI."""
        ...

    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        ...

    async def is_valid(self, jti: str) -> bool:
        """Check if a token is valid."""
        ...

    async def cleanup_expired(self) -> int:
        """Remove expired tokens."""
        ...


class RefreshTokenStore(ABC):
    """Abstract base class for refresh token storage.

    Provides interface for storing, retrieving, and revoking
    refresh tokens with TTL support.
    """

    @abstractmethod
    async def store(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        """Store a refresh token.

        Args:
            jti: JWT ID (unique token identifier).
            user_id: User who owns the token.
            expires_at: When the token expires.
        """
        ...

    @abstractmethod
    async def get(self, jti: str) -> StoredToken | None:
        """Get a stored token by JTI.

        Args:
            jti: JWT ID to look up.

        Returns:
            StoredToken if found, None otherwise.
        """
        ...

    @abstractmethod
    async def revoke(self, jti: str) -> bool:
        """Revoke a token by JTI.

        Args:
            jti: JWT ID to revoke.

        Returns:
            True if token was found and revoked, False otherwise.
        """
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all tokens for a user (logout from all devices).

        Args:
            user_id: User whose tokens should be revoked.

        Returns:
            Number of tokens revoked.
        """
        ...

    @abstractmethod
    async def is_valid(self, jti: str) -> bool:
        """Check if a token is valid (exists, not expired, not revoked).

        Args:
            jti: JWT ID to check.

        Returns:
            True if token is valid, False otherwise.
        """
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove expired tokens from storage.

        Returns:
            Number of tokens removed.
        """
        ...


class InMemoryTokenStore(RefreshTokenStore):
    """In-memory token store for development and testing.

    Not suitable for production - tokens are lost on restart
    and not shared across instances.
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._tokens: dict[str, StoredToken] = {}
        self._user_tokens: dict[str, set[str]] = {}

    async def store(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        """Store a refresh token in memory."""
        token = StoredToken(
            jti=jti,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            revoked=False,
        )
        self._tokens[jti] = token

        if user_id not in self._user_tokens:
            self._user_tokens[user_id] = set()
        self._user_tokens[user_id].add(jti)

        logger.debug(f"Stored refresh token {jti} for user {user_id}")

    async def get(self, jti: str) -> StoredToken | None:
        """Get a stored token by JTI."""
        return self._tokens.get(jti)

    async def revoke(self, jti: str) -> bool:
        """Revoke a token by JTI."""
        token = self._tokens.get(jti)
        if token is None:
            return False

        # Create new token with revoked=True (immutable dataclass)
        self._tokens[jti] = StoredToken(
            jti=token.jti,
            user_id=token.user_id,
            created_at=token.created_at,
            expires_at=token.expires_at,
            revoked=True,
        )

        logger.debug(f"Revoked refresh token {jti}")
        return True

    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        jtis = self._user_tokens.get(user_id, set())
        count = 0

        for jti in jtis:
            if await self.revoke(jti):
                count += 1

        logger.debug(f"Revoked {count} tokens for user {user_id}")
        return count

    async def is_valid(self, jti: str) -> bool:
        """Check if a token is valid."""
        token = self._tokens.get(jti)
        if token is None:
            return False
        return token.is_valid()

    async def cleanup_expired(self) -> int:
        """Remove expired tokens from storage."""
        expired_jtis = [
            jti for jti, token in self._tokens.items() if token.is_expired()
        ]

        for jti in expired_jtis:
            token = self._tokens.pop(jti, None)
            if token:
                user_jtis = self._user_tokens.get(token.user_id)
                if user_jtis:
                    user_jtis.discard(jti)

        logger.debug(f"Cleaned up {len(expired_jtis)} expired tokens")
        return len(expired_jtis)


class RedisTokenStore(RefreshTokenStore):
    """Redis-based token store for production use.

    Provides distributed token storage with automatic TTL expiration.
    Supports token revocation with blacklist persistence.

    **Feature: api-architecture-review**
    **Validates: Requirements 2.10**
    """

    KEY_PREFIX = "refresh_token:"
    USER_TOKENS_PREFIX = "user_tokens:"
    REVOKED_PREFIX = "revoked:"

    def __init__(self, redis_client: Any, default_ttl: int = 604800) -> None:
        """Initialize Redis token store.

        Args:
            redis_client: Async Redis client instance.
            default_ttl: Default TTL in seconds (7 days).
        """
        self._redis = redis_client
        self._default_ttl = default_ttl

    async def is_revoked(self, jti: str) -> bool:
        """Check if a token JTI is in the revocation blacklist.

        Args:
            jti: JWT ID to check.

        Returns:
            True if token is revoked, False otherwise.
        """
        return await self._redis.exists(f"{self.REVOKED_PREFIX}{jti}") > 0

    async def add_to_blacklist(self, jti: str, ttl: int) -> None:
        """Add a token JTI to the revocation blacklist.

        Args:
            jti: JWT ID to blacklist.
            ttl: Time-to-live in seconds (should match token expiration).
        """
        await self._redis.setex(f"{self.REVOKED_PREFIX}{jti}", ttl, "1")
        logger.debug(f"Added token {jti} to blacklist with TTL {ttl}s")

    def _token_key(self, jti: str) -> str:
        """Get Redis key for a token."""
        return f"{self.KEY_PREFIX}{jti}"

    def _user_key(self, user_id: str) -> str:
        """Get Redis key for user's token set."""
        return f"{self.USER_TOKENS_PREFIX}{user_id}"

    async def store(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        """Store a refresh token in Redis."""
        import json

        token = StoredToken(
            jti=jti,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            revoked=False,
        )

        # Calculate TTL from expiration
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl <= 0:
            ttl = self._default_ttl

        # Store token data
        await self._redis.setex(
            self._token_key(jti),
            ttl,
            json.dumps(token.to_dict()),
        )

        # Add to user's token set
        await self._redis.sadd(self._user_key(user_id), jti)

        logger.debug(f"Stored refresh token {jti} for user {user_id} with TTL {ttl}s")

    async def get(self, jti: str) -> StoredToken | None:
        """Get a stored token by JTI from Redis."""
        import json

        data = await self._redis.get(self._token_key(jti))
        if data is None:
            return None

        return StoredToken.from_dict(json.loads(data))

    async def revoke(self, jti: str) -> bool:
        """Revoke a token by JTI in Redis."""
        import json

        key = self._token_key(jti)
        data = await self._redis.get(key)

        if data is None:
            return False

        token = StoredToken.from_dict(json.loads(data))

        # Update with revoked=True
        revoked_token = StoredToken(
            jti=token.jti,
            user_id=token.user_id,
            created_at=token.created_at,
            expires_at=token.expires_at,
            revoked=True,
        )

        # Get remaining TTL
        ttl = await self._redis.ttl(key)
        if ttl > 0:
            await self._redis.setex(key, ttl, json.dumps(revoked_token.to_dict()))
        else:
            await self._redis.delete(key)

        logger.debug(f"Revoked refresh token {jti}")
        return True

    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all tokens for a user in Redis."""
        user_key = self._user_key(user_id)
        jtis = await self._redis.smembers(user_key)

        count = 0
        for jti in jtis:
            jti_str = jti.decode() if isinstance(jti, bytes) else jti
            if await self.revoke(jti_str):
                count += 1

        logger.debug(f"Revoked {count} tokens for user {user_id}")
        return count

    async def is_valid(self, jti: str) -> bool:
        """Check if a token is valid in Redis."""
        token = await self.get(jti)
        if token is None:
            return False
        return token.is_valid()

    async def cleanup_expired(self) -> int:
        """Redis handles TTL expiration automatically.

        This method is a no-op for Redis but included for interface compatibility.
        """
        return 0


async def create_token_store() -> RefreshTokenStore:
    """Factory function to create the appropriate token store.

    Creates RedisTokenStore if Redis is enabled in configuration,
    otherwise falls back to InMemoryTokenStore.

    **Feature: api-architecture-review**
    **Validates: Requirements 2.10**

    Returns:
        RefreshTokenStore: Configured token store instance.
    """
    from my_api.core.config import get_settings

    settings = get_settings()

    if settings.redis.enabled:
        try:
            import redis.asyncio as redis

            client = redis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await client.ping()
            logger.info(f"Connected to Redis at {settings.redis.url}")
            return RedisTokenStore(client, settings.redis.token_ttl)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory store.")
            return InMemoryTokenStore()
    else:
        logger.info("Redis disabled, using in-memory token store")
        return InMemoryTokenStore()


def get_token_store_sync() -> RefreshTokenStore:
    """Get token store synchronously (for non-async contexts).

    Returns InMemoryTokenStore by default. For Redis, use create_token_store().

    Returns:
        RefreshTokenStore: In-memory token store instance.
    """
    return InMemoryTokenStore()
