"""Unit tests for core/base/patterns/pagination.py.

Tests cursor-based pagination utilities.

**Feature: test-coverage-90-percent**
**Validates: Requirements 3.1**
"""

import base64
import json
from dataclasses import dataclass
from datetime import datetime

import pytest

from core.base.patterns.pagination import CursorPage, CursorPagination


@dataclass
class TestEntity:
    """Test entity for pagination."""
    
    id: str
    created_at: str
    name: str


class TestCursorPage:
    """Tests for CursorPage dataclass."""

    def test_create_cursor_page(self) -> None:
        """CursorPage should store pagination data."""
        items = [TestEntity(id="1", created_at="2024-01-01", name="Item 1")]
        page = CursorPage(
            items=items,
            next_cursor="next123",
            prev_cursor="prev123",
            has_more=True
        )
        
        assert page.items == items
        assert page.next_cursor == "next123"
        assert page.prev_cursor == "prev123"
        assert page.has_more is True

    def test_cursor_page_no_more(self) -> None:
        """CursorPage should handle last page."""
        page = CursorPage(
            items=[],
            next_cursor=None,
            prev_cursor="prev123",
            has_more=False
        )
        
        assert page.next_cursor is None
        assert page.has_more is False

    def test_cursor_page_first_page(self) -> None:
        """CursorPage should handle first page."""
        page = CursorPage(
            items=[TestEntity(id="1", created_at="2024-01-01", name="Item 1")],
            next_cursor="next123",
            prev_cursor=None,
            has_more=True
        )
        
        assert page.prev_cursor is None


class TestCursorPagination:
    """Tests for CursorPagination class."""

    def test_init_with_defaults(self) -> None:
        """CursorPagination should initialize with defaults."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["created_at", "id"]
        )
        
        assert pagination._cursor_fields == ["created_at", "id"]
        assert pagination._default_limit == 20

    def test_init_with_custom_limit(self) -> None:
        """CursorPagination should accept custom limit."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["id"],
            default_limit=50
        )
        
        assert pagination._default_limit == 50

    def test_encode_cursor(self) -> None:
        """encode_cursor should create base64 encoded cursor."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["created_at", "id"]
        )
        entity = TestEntity(id="123", created_at="2024-01-01", name="Test")
        
        cursor = pagination.encode_cursor(entity)
        
        # Decode and verify
        decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        assert decoded["id"] == "123"
        assert decoded["created_at"] == "2024-01-01"

    def test_encode_cursor_single_field(self) -> None:
        """encode_cursor should work with single field."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["id"]
        )
        entity = TestEntity(id="456", created_at="2024-01-01", name="Test")
        
        cursor = pagination.encode_cursor(entity)
        
        decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        assert decoded == {"id": "456"}

    def test_encode_cursor_missing_field(self) -> None:
        """encode_cursor should skip missing fields."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["id", "nonexistent"]
        )
        entity = TestEntity(id="789", created_at="2024-01-01", name="Test")
        
        cursor = pagination.encode_cursor(entity)
        
        decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        assert "id" in decoded
        assert "nonexistent" not in decoded

    def test_decode_cursor(self) -> None:
        """decode_cursor should decode base64 cursor."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["created_at", "id"]
        )
        cursor_data = {"id": "123", "created_at": "2024-01-01"}
        cursor = base64.urlsafe_b64encode(json.dumps(cursor_data).encode()).decode()
        
        decoded = pagination.decode_cursor(cursor)
        
        assert decoded["id"] == "123"
        assert decoded["created_at"] == "2024-01-01"

    def test_decode_cursor_invalid_base64(self) -> None:
        """decode_cursor should return empty dict for invalid base64."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["id"]
        )
        
        decoded = pagination.decode_cursor("not-valid-base64!!!")
        
        assert decoded == {}

    def test_decode_cursor_invalid_json(self) -> None:
        """decode_cursor should return empty dict for invalid JSON."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["id"]
        )
        invalid_cursor = base64.urlsafe_b64encode(b"not json").decode()
        
        decoded = pagination.decode_cursor(invalid_cursor)
        
        assert decoded == {}

    def test_encode_decode_roundtrip(self) -> None:
        """encode then decode should return original values."""
        pagination = CursorPagination[TestEntity, dict](
            cursor_fields=["created_at", "id"]
        )
        entity = TestEntity(id="roundtrip-123", created_at="2024-06-15", name="Test")
        
        cursor = pagination.encode_cursor(entity)
        decoded = pagination.decode_cursor(cursor)
        
        assert decoded["id"] == "roundtrip-123"
        assert decoded["created_at"] == "2024-06-15"

    def test_encode_cursor_none_value(self) -> None:
        """encode_cursor should skip None values."""
        @dataclass
        class EntityWithNone:
            id: str
            optional_field: str | None = None
        
        pagination = CursorPagination[EntityWithNone, dict](
            cursor_fields=["id", "optional_field"]
        )
        entity = EntityWithNone(id="123", optional_field=None)
        
        cursor = pagination.encode_cursor(entity)
        decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        
        assert "id" in decoded
        assert "optional_field" not in decoded
