"""Tests for cursor-based pagination module."""

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from core.base.patterns.pagination import CursorPage, CursorPagination


@dataclass
class SampleEntity:
    """Sample entity for testing."""

    id: str
    name: str
    created_at: datetime


class TestCursorPage:
    """Tests for CursorPage dataclass."""

    def test_create_page(self) -> None:
        items = [SampleEntity(id="1", name="Test", created_at=datetime.now(UTC))]
        page = CursorPage(
            items=items,
            next_cursor="next123",
            prev_cursor="prev123",
            has_more=True,
        )
        assert len(page.items) == 1
        assert page.next_cursor == "next123"
        assert page.prev_cursor == "prev123"
        assert page.has_more is True

    def test_page_without_cursors(self) -> None:
        page = CursorPage(
            items=[],
            next_cursor=None,
            prev_cursor=None,
            has_more=False,
        )
        assert page.next_cursor is None
        assert page.prev_cursor is None
        assert page.has_more is False

    def test_page_is_frozen(self) -> None:
        page = CursorPage(items=[], next_cursor=None, prev_cursor=None, has_more=False)
        with pytest.raises(AttributeError):
            page.has_more = True  # type: ignore


class TestCursorPagination:
    """Tests for CursorPagination class."""

    def test_init_with_defaults(self) -> None:
        pagination = CursorPagination(cursor_fields=["id"])
        assert pagination._cursor_fields == ["id"]
        assert pagination._default_limit == 20

    def test_init_with_custom_limit(self) -> None:
        pagination = CursorPagination(cursor_fields=["id"], default_limit=50)
        assert pagination._default_limit == 50

    def test_init_with_multiple_fields(self) -> None:
        pagination = CursorPagination(cursor_fields=["created_at", "id"])
        assert pagination._cursor_fields == ["created_at", "id"]

    def test_encode_cursor_single_field(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id"])
        entity = SampleEntity(id="123", name="Test", created_at=datetime.now(UTC))
        cursor = pagination.encode_cursor(entity)
        assert isinstance(cursor, str)
        # Decode and verify
        decoded = json.loads(base64.urlsafe_b64decode(cursor))
        assert decoded["id"] == "123"

    def test_encode_cursor_multiple_fields(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id", "name"])
        entity = SampleEntity(id="123", name="Test", created_at=datetime.now(UTC))
        cursor = pagination.encode_cursor(entity)
        decoded = json.loads(base64.urlsafe_b64decode(cursor))
        assert decoded["id"] == "123"
        assert decoded["name"] == "Test"

    def test_encode_cursor_skips_none_values(self) -> None:
        @dataclass
        class EntityWithOptional:
            id: str
            optional: str | None = None

        pagination = CursorPagination[EntityWithOptional, dict](cursor_fields=["id", "optional"])
        entity = EntityWithOptional(id="123", optional=None)
        cursor = pagination.encode_cursor(entity)
        decoded = json.loads(base64.urlsafe_b64decode(cursor))
        assert "id" in decoded
        assert "optional" not in decoded

    def test_decode_cursor_valid(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id"])
        # Create a valid cursor
        cursor_data = {"id": "123", "name": "Test"}
        cursor = base64.urlsafe_b64encode(json.dumps(cursor_data).encode()).decode()
        result = pagination.decode_cursor(cursor)
        assert result["id"] == "123"
        assert result["name"] == "Test"

    def test_decode_cursor_invalid_base64(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id"])
        result = pagination.decode_cursor("not-valid-base64!!!")
        assert result == {}

    def test_decode_cursor_invalid_json(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id"])
        # Valid base64 but invalid JSON
        cursor = base64.urlsafe_b64encode(b"not json").decode()
        result = pagination.decode_cursor(cursor)
        assert result == {}

    def test_encode_decode_roundtrip(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id", "name"])
        entity = SampleEntity(id="abc-123", name="Test Entity", created_at=datetime.now(UTC))
        cursor = pagination.encode_cursor(entity)
        decoded = pagination.decode_cursor(cursor)
        assert decoded["id"] == "abc-123"
        assert decoded["name"] == "Test Entity"

    def test_cursor_is_url_safe(self) -> None:
        pagination = CursorPagination[SampleEntity, dict](cursor_fields=["id"])
        entity = SampleEntity(id="test/with/slashes", name="Test", created_at=datetime.now(UTC))
        cursor = pagination.encode_cursor(entity)
        # URL-safe base64 should not contain + or /
        assert "+" not in cursor
        assert "/" not in cursor
