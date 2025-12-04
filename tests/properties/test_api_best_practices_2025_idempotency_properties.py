"""Property-based tests for API idempotency.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 23.1, 23.2, 23.3, 23.4, 23.5**

Property tests for:
- Property 11: Idempotency Key Replay
- Property 12: Idempotency Key Conflict Detection
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from infrastructure.idempotency import (
    IdempotencyHandler,
    IdempotencyRecord,
    IdempotencyConfig,
    IdempotencyKeyConflictError,
)
from infrastructure.idempotency.handler import compute_request_hash


# === Test Fixtures ===


@pytest.fixture
def idempotency_config() -> IdempotencyConfig:
    """Default idempotency configuration."""
    return IdempotencyConfig(
        ttl_hours=24,
        key_prefix="test-idempotency",
        header_name="Idempotency-Key",
    )


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock()
    mock.delete = AsyncMock(return_value=1)
    return mock


@pytest.fixture
def handler_with_mock_redis(
    idempotency_config: IdempotencyConfig,
    mock_redis: AsyncMock,
) -> IdempotencyHandler:
    """Idempotency handler with mocked Redis."""
    handler = IdempotencyHandler(config=idempotency_config)
    handler._redis = mock_redis
    handler._connected = True
    return handler


# === Strategies ===


idempotency_key_strategy = st.uuids().map(str)

request_body_strategy = st.dictionaries(
    st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
    st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
    min_size=1,
    max_size=5,
)


# === Property Tests ===


class TestIdempotencyKeyReplay:
    """Property 11: Idempotency Key Replay.

    For any request with an Idempotency-Key header, sending the same request
    multiple times SHALL return the same response without re-executing the operation.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.1, 23.3**
    """

    @settings(max_examples=50, deadline=None)
    @given(
        idempotency_key=idempotency_key_strategy,
        request_body=request_body_strategy,
    )
    @pytest.mark.asyncio
    async def test_duplicate_request_returns_cached_response(
        self,
        idempotency_key: str,
        request_body: dict,
    ) -> None:
        """Duplicate requests SHALL return cached response.

        **Feature: api-best-practices-review-2025, Property 11: Idempotency Key Replay**
        **Validates: Requirements 23.1, 23.3**
        """
        # Setup
        stored_record: dict | None = None
        
        async def mock_get(key: str) -> str | None:
            if stored_record:
                return json.dumps(stored_record)
            return None
        
        async def mock_setex(key: str, ttl: int, value: str) -> None:
            nonlocal stored_record
            stored_record = json.loads(value)
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        handler = IdempotencyHandler()
        handler._redis = mock_redis
        handler._connected = True
        
        # Compute request hash
        body_bytes = json.dumps(request_body).encode()
        request_hash = compute_request_hash("POST", "/api/test", body_bytes)
        
        # Track operation execution count
        execution_count = 0
        
        async def operation() -> tuple[str, int]:
            nonlocal execution_count
            execution_count += 1
            return json.dumps({"result": "success"}), 200
        
        # First request
        body1, status1, is_replay1 = await handler.execute_idempotent(
            idempotency_key, request_hash, operation
        )
        
        # Second request (duplicate)
        body2, status2, is_replay2 = await handler.execute_idempotent(
            idempotency_key, request_hash, operation
        )
        
        # Assertions
        assert execution_count == 1, "Operation should execute only once"
        assert is_replay1 is False, "First request should not be replay"
        assert is_replay2 is True, "Second request should be replay"
        assert body1 == body2, "Responses should be identical"
        assert status1 == status2, "Status codes should be identical"

    @settings(max_examples=20, deadline=None)
    @given(idempotency_key=idempotency_key_strategy)
    @pytest.mark.asyncio
    async def test_replay_preserves_status_code(
        self,
        idempotency_key: str,
    ) -> None:
        """Replayed response SHALL preserve original status code.

        **Feature: api-best-practices-review-2025, Property 11**
        """
        stored_record: dict | None = None
        
        async def mock_get(key: str) -> str | None:
            if stored_record:
                return json.dumps(stored_record)
            return None
        
        async def mock_setex(key: str, ttl: int, value: str) -> None:
            nonlocal stored_record
            stored_record = json.loads(value)
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        handler = IdempotencyHandler()
        handler._redis = mock_redis
        handler._connected = True
        
        request_hash = compute_request_hash("POST", "/api/test", b"{}")
        
        # Operation returns 201 Created
        async def operation() -> tuple[str, int]:
            return json.dumps({"id": "123"}), 201
        
        # First request
        _, status1, _ = await handler.execute_idempotent(
            idempotency_key, request_hash, operation
        )
        
        # Second request
        _, status2, is_replay = await handler.execute_idempotent(
            idempotency_key, request_hash, operation
        )
        
        assert status1 == 201
        assert status2 == 201
        assert is_replay is True


class TestIdempotencyKeyConflict:
    """Property 12: Idempotency Key Conflict Detection.

    For any Idempotency-Key, using the same key with a different request body
    SHALL result in a 422 error.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.4**
    """

    @settings(max_examples=50, deadline=None)
    @given(
        idempotency_key=idempotency_key_strategy,
        body1=request_body_strategy,
        body2=request_body_strategy,
    )
    @pytest.mark.asyncio
    async def test_different_body_raises_conflict(
        self,
        idempotency_key: str,
        body1: dict,
        body2: dict,
    ) -> None:
        """Different request body with same key SHALL raise conflict.

        **Feature: api-best-practices-review-2025, Property 12: Idempotency Key Conflict**
        **Validates: Requirements 23.4**
        """
        # Skip if bodies happen to be equal
        if body1 == body2:
            return
        
        stored_record: dict | None = None
        
        async def mock_get(key: str) -> str | None:
            if stored_record:
                return json.dumps(stored_record)
            return None
        
        async def mock_setex(key: str, ttl: int, value: str) -> None:
            nonlocal stored_record
            stored_record = json.loads(value)
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.get = mock_get
        mock_redis.setex = mock_setex
        
        handler = IdempotencyHandler()
        handler._redis = mock_redis
        handler._connected = True
        
        # Compute different hashes for different bodies
        hash1 = compute_request_hash("POST", "/api/test", json.dumps(body1).encode())
        hash2 = compute_request_hash("POST", "/api/test", json.dumps(body2).encode())
        
        async def operation() -> tuple[str, int]:
            return json.dumps({"result": "success"}), 200
        
        # First request succeeds
        await handler.execute_idempotent(idempotency_key, hash1, operation)
        
        # Second request with different body should raise conflict
        with pytest.raises(IdempotencyKeyConflictError) as exc_info:
            await handler.execute_idempotent(idempotency_key, hash2, operation)
        
        assert exc_info.value.idempotency_key == idempotency_key

    @pytest.mark.asyncio
    async def test_conflict_error_message(self) -> None:
        """Conflict error SHALL contain idempotency key.

        **Feature: api-best-practices-review-2025, Property 12**
        """
        error = IdempotencyKeyConflictError("test-key-123")
        
        assert "test-key-123" in str(error)
        assert error.idempotency_key == "test-key-123"


class TestRequestHashComputation:
    """Tests for request hash computation.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.4**
    """

    @settings(max_examples=50, deadline=None)
    @given(
        method=st.sampled_from(["POST", "PATCH", "PUT"]),
        path=st.text(min_size=1, max_size=50),
        body=st.binary(min_size=0, max_size=1000),
    )
    def test_hash_deterministic(
        self,
        method: str,
        path: str,
        body: bytes,
    ) -> None:
        """Same request SHALL produce same hash.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.4**
        """
        hash1 = compute_request_hash(method, path, body)
        hash2 = compute_request_hash(method, path, body)
        
        assert hash1 == hash2, "Hash must be deterministic"

    @settings(max_examples=50, deadline=None)
    @given(
        body1=st.binary(min_size=1, max_size=100),
        body2=st.binary(min_size=1, max_size=100),
    )
    def test_different_bodies_different_hashes(
        self,
        body1: bytes,
        body2: bytes,
    ) -> None:
        """Different bodies SHALL produce different hashes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.4**
        """
        if body1 == body2:
            return
        
        hash1 = compute_request_hash("POST", "/api/test", body1)
        hash2 = compute_request_hash("POST", "/api/test", body2)
        
        assert hash1 != hash2, "Different bodies must have different hashes"

    def test_method_affects_hash(self) -> None:
        """Different methods SHALL produce different hashes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.4**
        """
        body = b'{"data": "test"}'
        
        hash_post = compute_request_hash("POST", "/api/test", body)
        hash_patch = compute_request_hash("PATCH", "/api/test", body)
        
        assert hash_post != hash_patch

    def test_path_affects_hash(self) -> None:
        """Different paths SHALL produce different hashes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.4**
        """
        body = b'{"data": "test"}'
        
        hash1 = compute_request_hash("POST", "/api/v1/users", body)
        hash2 = compute_request_hash("POST", "/api/v1/orders", body)
        
        assert hash1 != hash2


class TestIdempotencyRecord:
    """Tests for IdempotencyRecord serialization.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.2**
    """

    @settings(max_examples=50, deadline=None)
    @given(
        idempotency_key=idempotency_key_strategy,
        status_code=st.sampled_from([200, 201, 202, 204]),
    )
    def test_record_round_trip(
        self,
        idempotency_key: str,
        status_code: int,
    ) -> None:
        """Record serialization/deserialization SHALL preserve data.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.2**
        """
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            request_hash="abc123",
            response_body='{"result": "success"}',
            status_code=status_code,
        )
        
        # Round-trip through dict
        record_dict = record.to_dict()
        restored = IdempotencyRecord.from_dict(record_dict)
        
        assert restored.idempotency_key == record.idempotency_key
        assert restored.request_hash == record.request_hash
        assert restored.response_body == record.response_body
        assert restored.status_code == record.status_code


class TestIdempotencyConfig:
    """Tests for IdempotencyConfig.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.2**
    """

    def test_default_config(self) -> None:
        """Default config SHALL have reasonable defaults."""
        config = IdempotencyConfig()
        
        assert config.ttl_hours == 24
        assert config.header_name == "Idempotency-Key"
        assert config.key_prefix == "idempotency"

    def test_custom_config(self) -> None:
        """Custom config SHALL be applied."""
        config = IdempotencyConfig(
            ttl_hours=48,
            key_prefix="custom-prefix",
            header_name="X-Idempotency-Key",
        )
        
        assert config.ttl_hours == 48
        assert config.key_prefix == "custom-prefix"
        assert config.header_name == "X-Idempotency-Key"
