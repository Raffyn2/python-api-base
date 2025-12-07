"""Tests for audit trail module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from dataclasses import dataclass
from datetime import datetime

import pytest
from pydantic import BaseModel

from infrastructure.audit.trail import (
    AuditAction,
    AuditRecord,
    compute_changes,
)


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""

    name: str
    value: int


@dataclass
class SampleDataclass:
    """Sample dataclass for testing."""

    name: str
    value: int


class TestAuditAction:
    """Tests for AuditAction enum."""

    def test_create_action(self) -> None:
        """Test CREATE action value."""
        assert AuditAction.CREATE.value == "CREATE"

    def test_read_action(self) -> None:
        """Test READ action value."""
        assert AuditAction.READ.value == "READ"

    def test_update_action(self) -> None:
        """Test UPDATE action value."""
        assert AuditAction.UPDATE.value == "UPDATE"

    def test_delete_action(self) -> None:
        """Test DELETE action value."""
        assert AuditAction.DELETE.value == "DELETE"

    def test_all_actions_exist(self) -> None:
        """Test all expected actions exist."""
        expected = [
            "CREATE", "READ", "UPDATE", "DELETE", "RESTORE",
            "LOGIN", "LOGOUT", "ACCESS_DENIED", "EXPORT", "IMPORT"
        ]
        actual = [a.value for a in AuditAction]
        assert set(expected) == set(actual)


class TestAuditRecord:
    """Tests for AuditRecord dataclass."""

    def test_create_with_defaults(self) -> None:
        """Test creating with default values."""
        record = AuditRecord()
        assert record.id is not None
        assert record.entity_type == ""
        assert record.entity_id == ""
        assert record.action == AuditAction.READ
        assert record.user_id is None
        assert record.correlation_id is None
        assert record.before is None
        assert record.after is None
        assert record.changes == {}
        assert record.metadata == {}

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        now = datetime.now()
        record = AuditRecord(
            id="audit-123",
            entity_type="User",
            entity_id="user-456",
            action=AuditAction.UPDATE,
            user_id="admin-001",
            correlation_id="corr-789",
            timestamp=now,
            before={"name": "old"},
            after={"name": "new"},
            changes={"name": ("old", "new")},
            metadata={"source": "api"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert record.id == "audit-123"
        assert record.entity_type == "User"
        assert record.entity_id == "user-456"
        assert record.action == AuditAction.UPDATE
        assert record.user_id == "admin-001"
        assert record.ip_address == "192.168.1.1"
        assert record.user_agent == "Mozilla/5.0"

    def test_get_changed_fields(self) -> None:
        """Test get_changed_fields method."""
        record = AuditRecord(
            changes={
                "name": ("old", "new"),
                "email": ("old@test.com", "new@test.com"),
            }
        )
        fields = record.get_changed_fields()
        assert set(fields) == {"name", "email"}

    def test_get_changed_fields_empty(self) -> None:
        """Test get_changed_fields with no changes."""
        record = AuditRecord()
        assert record.get_changed_fields() == []

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        now = datetime.now()
        record = AuditRecord(
            id="audit-123",
            entity_type="User",
            entity_id="user-456",
            action=AuditAction.CREATE,
            user_id="admin-001",
            timestamp=now,
            changes={"name": ("old", "new")},
        )
        result = record.to_dict()
        assert result["id"] == "audit-123"
        assert result["entity_type"] == "User"
        assert result["action"] == "CREATE"
        assert result["timestamp"] == now.isoformat()
        assert result["changes"]["name"] == {"old": "old", "new": "new"}

    def test_to_dict_with_pydantic_snapshot(self) -> None:
        """Test to_dict with Pydantic model snapshot."""
        model = SampleModel(name="test", value=42)
        record = AuditRecord(after=model)
        result = record.to_dict()
        assert result["after"] == {"name": "test", "value": 42}

    def test_to_dict_with_dataclass_snapshot(self) -> None:
        """Test to_dict with dataclass snapshot."""
        obj = SampleDataclass(name="test", value=42)
        record = AuditRecord(after=obj)
        result = record.to_dict()
        assert result["after"]["name"] == "test"
        assert result["after"]["value"] == 42

    def test_to_dict_with_primitive_snapshot(self) -> None:
        """Test to_dict with primitive snapshot."""
        record = AuditRecord(after="simple_value")
        result = record.to_dict()
        assert result["after"] == {"value": "simple_value"}

    def test_to_dict_with_none_snapshot(self) -> None:
        """Test to_dict with None snapshot."""
        record = AuditRecord()
        result = record.to_dict()
        assert result["before"] is None
        assert result["after"] is None

    def test_frozen_dataclass(self) -> None:
        """Test that AuditRecord is immutable."""
        record = AuditRecord()
        with pytest.raises(AttributeError):
            record.entity_type = "new_type"


class TestComputeChanges:
    """Tests for compute_changes function."""

    def test_both_none(self) -> None:
        """Test with both before and after as None."""
        result = compute_changes(None, None)
        assert result == {}

    def test_creation_from_none(self) -> None:
        """Test creation (before is None)."""
        after = SampleModel(name="test", value=42)
        result = compute_changes(None, after)
        assert result["name"] == (None, "test")
        assert result["value"] == (None, 42)

    def test_deletion_to_none(self) -> None:
        """Test deletion (after is None)."""
        before = SampleModel(name="test", value=42)
        result = compute_changes(before, None)
        assert result["name"] == ("test", None)
        assert result["value"] == (42, None)

    def test_update_with_changes(self) -> None:
        """Test update with actual changes."""
        before = SampleModel(name="old", value=10)
        after = SampleModel(name="new", value=20)
        result = compute_changes(before, after)
        assert result["name"] == ("old", "new")
        assert result["value"] == (10, 20)

    def test_update_partial_changes(self) -> None:
        """Test update with partial changes."""
        before = SampleModel(name="same", value=10)
        after = SampleModel(name="same", value=20)
        result = compute_changes(before, after)
        assert "name" not in result
        assert result["value"] == (10, 20)

    def test_update_no_changes(self) -> None:
        """Test update with no changes."""
        before = SampleModel(name="same", value=42)
        after = SampleModel(name="same", value=42)
        result = compute_changes(before, after)
        assert result == {}

    def test_with_non_basemodel_before_none(self) -> None:
        """Test with non-BaseModel when before is None."""
        result = compute_changes(None, "not_a_model")
        assert result == {}

    def test_with_non_basemodel_after_none(self) -> None:
        """Test with non-BaseModel when after is None."""
        result = compute_changes("not_a_model", None)
        assert result == {}
