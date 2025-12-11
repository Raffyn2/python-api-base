"""Idempotency handler for API operations.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 23.1, 23.2, 23.3, 23.4**

Implements:
- Idempotency-Key header support for POST/PATCH operations
- Redis-based storage with configurable TTL (24-48 hours)
- Request body hash comparison for conflict detection
- Cached response return for duplicate requests
"""

import contextlib
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Self

import structlog

from infrastructure.idempotency.errors import IdempotencyKeyConflictError

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """Record of an idempotent operation.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.2**

    Stores:
    - Request hash for conflict detection
    - Response body and status for replay
    - Timestamps for TTL and debugging
    """

    idempotency_key: str
    request_hash: str
    response_body: str
    status_code: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "idempotency_key": self.idempotency_key,
            "request_hash": self.request_hash,
            "response_body": self.response_body,
            "status_code": self.status_code,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            idempotency_key=data["idempotency_key"],
            request_hash=data["request_hash"],
            response_body=data["response_body"],
            status_code=data["status_code"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass(slots=True)
class IdempotencyConfig:
    """Configuration for idempotency handling.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.2**
    """

    # TTL for idempotency records (24-48 hours recommended)
    ttl_hours: int = 24

    # Redis key prefix
    key_prefix: str = "idempotency"

    # Header name for idempotency key
    header_name: str = "Idempotency-Key"

    # Endpoints that require idempotency key
    required_endpoints: set[str] = field(default_factory=set)

    # Response header for replayed requests
    replay_header: str = "X-Idempotent-Replayed"


def compute_request_hash(
    method: str,
    path: str,
    body: bytes,
    content_type: str | None = None,
) -> str:
    """Compute hash of request for comparison.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.4**

    Args:
        method: HTTP method.
        path: Request path.
        body: Request body bytes.
        content_type: Content-Type header.

    Returns:
        SHA-256 hash of request.
    """
    hasher = hashlib.sha256()
    hasher.update(method.encode())
    hasher.update(path.encode())
    hasher.update(body)
    if content_type:
        hasher.update(content_type.encode())
    return hasher.hexdigest()


class IdempotencyHandler:
    """Handler for idempotent API operations.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.1, 23.2, 23.3, 23.4**

    Ensures that POST/PATCH operations with the same Idempotency-Key
    return the same response without re-executing the operation.

    Example:
        >>> handler = IdempotencyHandler(redis_client)
        >>> # Check if request is duplicate
        >>> record = await handler.get_record(idempotency_key)
        >>> if record:
        ...     if record.request_hash != current_hash:
        ...         raise IdempotencyKeyConflictError(idempotency_key)
        ...     return record.response_body, record.status_code, True
        >>> # Execute operation and store result
        >>> response = await execute_operation()
        >>> await handler.store_record(
        ...     idempotency_key, request_hash, response.body, response.status_code
        ... )
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        config: IdempotencyConfig | None = None,
    ) -> None:
        """Initialize idempotency handler.

        Args:
            redis_url: Redis connection URL.
            config: Idempotency configuration.
        """
        self._redis_url = redis_url
        self._config = config or IdempotencyConfig()
        self._redis: Any = None
        self._connected = False
        self._ttl_seconds = self._config.ttl_hours * 3600

    async def connect(self) -> bool:
        """Connect to Redis.

        Returns:
            True if connected successfully.
        """
        client = await self._get_client()
        return client is not None

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis is not None:
            with contextlib.suppress(Exception):
                await self._redis.close()
            self._redis = None
            self._connected = False

    async def _get_client(self) -> Any | None:
        """Get or create Redis client."""
        if self._redis is not None and self._connected:
            return self._redis

        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._connected = True
            return self._redis
        except ImportError:
            logger.warning("redis package not installed")
            self._connected = False
            return None
        except Exception:
            logger.warning(
                "Redis connection failed",
                operation="IDEMPOTENCY_CONNECT",
            )
            self._connected = False
            return None

    def _make_key(self, idempotency_key: str) -> str:
        """Create full Redis key."""
        return f"{self._config.key_prefix}:{idempotency_key}"

    async def get_record(self, idempotency_key: str) -> IdempotencyRecord | None:
        """Get existing idempotency record.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.3**

        Args:
            idempotency_key: The Idempotency-Key header value.

        Returns:
            IdempotencyRecord if found, None otherwise.
        """
        client = await self._get_client()
        if client is None:
            return None

        try:
            full_key = self._make_key(idempotency_key)
            data = await client.get(full_key)

            if data is None:
                return None

            return IdempotencyRecord.from_dict(json.loads(data))
        except Exception:
            logger.warning(
                "Failed to get idempotency record",
                key=idempotency_key,
                operation="IDEMPOTENCY_GET",
            )
            return None

    async def store_record(
        self,
        idempotency_key: str,
        request_hash: str,
        response_body: str,
        status_code: int,
    ) -> bool:
        """Store idempotency record.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.2**

        Args:
            idempotency_key: The Idempotency-Key header value.
            request_hash: Hash of the request for conflict detection.
            response_body: Response body to store.
            status_code: HTTP status code.

        Returns:
            True if stored successfully.
        """
        client = await self._get_client()
        if client is None:
            return False

        try:
            record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_body=response_body,
                status_code=status_code,
            )

            full_key = self._make_key(idempotency_key)
            await client.setex(
                full_key,
                self._ttl_seconds,
                json.dumps(record.to_dict()),
            )

            logger.debug(
                "Stored idempotency record",
                key=idempotency_key,
                status=status_code,
            )
            return True
        except Exception:
            logger.warning(
                "Failed to store idempotency record",
                key=idempotency_key,
                operation="IDEMPOTENCY_STORE",
            )
            return False

    async def execute_idempotent(
        self,
        idempotency_key: str,
        request_hash: str,
        operation: Any,
    ) -> tuple[str, int, bool]:
        """Execute operation with idempotency.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.1, 23.3, 23.4**

        Args:
            idempotency_key: The Idempotency-Key header value.
            request_hash: Hash of the current request.
            operation: Async callable that returns (body, status_code).

        Returns:
            Tuple of (response_body, status_code, is_replay).

        Raises:
            IdempotencyKeyConflictError: If key is reused with different body.
        """
        # Check for existing record
        record = await self.get_record(idempotency_key)

        if record is not None:
            # Check for conflict
            if record.request_hash != request_hash:
                logger.warning(
                    "Idempotency key conflict",
                    key=idempotency_key,
                )
                raise IdempotencyKeyConflictError(idempotency_key)

            # Return cached response
            logger.info(
                "Replaying idempotent response",
                key=idempotency_key,
                status=record.status_code,
            )
            return record.response_body, record.status_code, True

        # Execute operation
        response_body, status_code = await operation()

        # Store result
        await self.store_record(
            idempotency_key,
            request_hash,
            response_body,
            status_code,
        )

        return response_body, status_code, False

    async def delete_record(self, idempotency_key: str) -> bool:
        """Delete an idempotency record.

        Useful for cleanup or testing.

        Args:
            idempotency_key: The Idempotency-Key header value.

        Returns:
            True if deleted.
        """
        client = await self._get_client()
        if client is None:
            return False

        try:
            full_key = self._make_key(idempotency_key)
            result = await client.delete(full_key)
            return result > 0
        except Exception:
            logger.warning(
                "Failed to delete idempotency record",
                key=idempotency_key,
                operation="IDEMPOTENCY_DELETE",
            )
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            self._connected = False
