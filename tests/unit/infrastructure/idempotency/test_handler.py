"""Tests for idempotency handler module."""

from datetime import UTC, datetime

import pytest

from infrastructure.idempotency.handler import (
    IdempotencyConfig,
    IdempotencyRecord,
    compute_request_hash,
)


class TestIdempotencyRecord:
    """Tests for IdempotencyRecord dataclass."""

    def test_create_record(self) -> None:
        record = IdempotencyRecord(
            idempotency_key="key-123",
            request_hash="abc123",
            response_body='{"id": 1}',
            status_code=201,
        )
        assert record.idempotency_key == "key-123"
        assert record.request_hash == "abc123"
        assert record.response_body == '{"id": 1}'
        assert record.status_code == 201

    def test_created_at_default(self) -> None:
        before = datetime.now(UTC)
        record = IdempotencyRecord(
            idempotency_key="key",
            request_hash="hash",
            response_body="body",
            status_code=200,
        )
        after = datetime.now(UTC)
        assert before <= record.created_at <= after

    def test_to_dict(self) -> None:
        record = IdempotencyRecord(
            idempotency_key="key-123",
            request_hash="abc123",
            response_body='{"id": 1}',
            status_code=201,
        )
        result = record.to_dict()
        assert result["idempotency_key"] == "key-123"
        assert result["request_hash"] == "abc123"
        assert result["response_body"] == '{"id": 1}'
        assert result["status_code"] == 201
        assert "created_at" in result

    def test_from_dict(self) -> None:
        data = {
            "idempotency_key": "key-123",
            "request_hash": "abc123",
            "response_body": '{"id": 1}',
            "status_code": 201,
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        record = IdempotencyRecord.from_dict(data)
        assert record.idempotency_key == "key-123"
        assert record.request_hash == "abc123"
        assert record.status_code == 201

    def test_roundtrip(self) -> None:
        original = IdempotencyRecord(
            idempotency_key="key-123",
            request_hash="abc123",
            response_body='{"id": 1}',
            status_code=201,
        )
        data = original.to_dict()
        restored = IdempotencyRecord.from_dict(data)
        assert restored.idempotency_key == original.idempotency_key
        assert restored.request_hash == original.request_hash
        assert restored.response_body == original.response_body
        assert restored.status_code == original.status_code

    def test_is_frozen(self) -> None:
        record = IdempotencyRecord(
            idempotency_key="key",
            request_hash="hash",
            response_body="body",
            status_code=200,
        )
        with pytest.raises(AttributeError):
            record.idempotency_key = "new-key"  # type: ignore


class TestIdempotencyConfig:
    """Tests for IdempotencyConfig dataclass."""

    def test_default_values(self) -> None:
        config = IdempotencyConfig()
        assert config.ttl_hours == 24
        assert config.key_prefix == "idempotency"
        assert config.header_name == "Idempotency-Key"
        assert config.replay_header == "X-Idempotent-Replayed"
        assert config.required_endpoints == set()

    def test_custom_ttl(self) -> None:
        config = IdempotencyConfig(ttl_hours=48)
        assert config.ttl_hours == 48

    def test_custom_key_prefix(self) -> None:
        config = IdempotencyConfig(key_prefix="idem")
        assert config.key_prefix == "idem"

    def test_custom_header_name(self) -> None:
        config = IdempotencyConfig(header_name="X-Request-Id")
        assert config.header_name == "X-Request-Id"

    def test_required_endpoints(self) -> None:
        endpoints = {"/api/payments", "/api/orders"}
        config = IdempotencyConfig(required_endpoints=endpoints)
        assert config.required_endpoints == endpoints


class TestComputeRequestHash:
    """Tests for compute_request_hash function."""

    def test_returns_string(self) -> None:
        result = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        assert isinstance(result, str)

    def test_returns_hex_hash(self) -> None:
        result = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        assert len(result) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_same_hash(self) -> None:
        hash1 = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        hash2 = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        assert hash1 == hash2

    def test_different_method_different_hash(self) -> None:
        hash1 = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        hash2 = compute_request_hash("PUT", "/api/users", b'{"name": "test"}')
        assert hash1 != hash2

    def test_different_path_different_hash(self) -> None:
        hash1 = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        hash2 = compute_request_hash("POST", "/api/orders", b'{"name": "test"}')
        assert hash1 != hash2

    def test_different_body_different_hash(self) -> None:
        hash1 = compute_request_hash("POST", "/api/users", b'{"name": "test1"}')
        hash2 = compute_request_hash("POST", "/api/users", b'{"name": "test2"}')
        assert hash1 != hash2

    def test_content_type_affects_hash(self) -> None:
        hash1 = compute_request_hash("POST", "/api/users", b'{"name": "test"}', "application/json")
        hash2 = compute_request_hash("POST", "/api/users", b'{"name": "test"}', "text/plain")
        assert hash1 != hash2

    def test_none_content_type(self) -> None:
        hash1 = compute_request_hash("POST", "/api/users", b'{"name": "test"}', None)
        hash2 = compute_request_hash("POST", "/api/users", b'{"name": "test"}')
        assert hash1 == hash2

    def test_empty_body(self) -> None:
        result = compute_request_hash("POST", "/api/users", b"")
        assert isinstance(result, str)
        assert len(result) == 64
