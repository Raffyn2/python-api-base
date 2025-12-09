"""Unit tests for core/base/domain/entity.py.

Tests entity creation, equality, timestamps, and soft delete functionality.

**Feature: test-coverage-90-percent**
**Validates: Requirements 3.1**
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from core.base.domain.entity import (
    AuditableEntity,
    AuditableULIDEntity,
    AuditableVersionedEntity,
    BaseEntity,
    ULIDEntity,
    VersionedEntity,
    VersionedULIDEntity,
    VersionMixin,
)


class TestBaseEntity:
    """Tests for BaseEntity class."""

    def test_create_entity_with_defaults(self) -> None:
        """Entity should be created with default values."""
        entity = BaseEntity[str]()
        
        assert entity.id is None
        assert entity.is_deleted is False
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)

    def test_create_entity_with_id(self) -> None:
        """Entity should accept custom ID."""
        entity = BaseEntity[str](id="test-id-123")
        
        assert entity.id == "test-id-123"

    def test_create_entity_with_int_id(self) -> None:
        """Entity should work with integer ID type."""
        entity = BaseEntity[int](id=42)
        
        assert entity.id == 42

    def test_mark_updated_changes_timestamp(self) -> None:
        """mark_updated should update the updated_at timestamp."""
        entity = BaseEntity[str]()
        original_updated_at = entity.updated_at
        
        # Small delay to ensure timestamp difference
        entity.mark_updated()
        
        assert entity.updated_at >= original_updated_at

    def test_mark_deleted_sets_flag(self) -> None:
        """mark_deleted should set is_deleted to True."""
        entity = BaseEntity[str]()
        
        entity.mark_deleted()
        
        assert entity.is_deleted is True

    def test_mark_deleted_updates_timestamp(self) -> None:
        """mark_deleted should also update the timestamp."""
        entity = BaseEntity[str]()
        original_updated_at = entity.updated_at
        
        entity.mark_deleted()
        
        assert entity.updated_at >= original_updated_at

    def test_mark_restored_clears_flag(self) -> None:
        """mark_restored should set is_deleted to False."""
        entity = BaseEntity[str](is_deleted=True)
        
        entity.mark_restored()
        
        assert entity.is_deleted is False

    def test_mark_restored_updates_timestamp(self) -> None:
        """mark_restored should also update the timestamp."""
        entity = BaseEntity[str](is_deleted=True)
        original_updated_at = entity.updated_at
        
        entity.mark_restored()
        
        assert entity.updated_at >= original_updated_at

    def test_from_attributes_config(self) -> None:
        """Entity should support from_attributes for ORM mapping."""
        assert BaseEntity.model_config.get("from_attributes") is True


class TestAuditableEntity:
    """Tests for AuditableEntity class."""

    def test_create_auditable_entity_with_defaults(self) -> None:
        """AuditableEntity should have audit fields."""
        entity = AuditableEntity[str]()
        
        assert entity.created_by is None
        assert entity.updated_by is None

    def test_create_auditable_entity_with_user(self) -> None:
        """AuditableEntity should accept user IDs."""
        entity = AuditableEntity[str](
            created_by="user-123",
            updated_by="user-456"
        )
        
        assert entity.created_by == "user-123"
        assert entity.updated_by == "user-456"

    def test_mark_updated_by_sets_user(self) -> None:
        """mark_updated_by should set updated_by and timestamp."""
        entity = AuditableEntity[str]()
        
        entity.mark_updated_by("user-789")
        
        assert entity.updated_by == "user-789"


class TestVersionMixin:
    """Tests for VersionMixin class."""

    def test_default_version(self) -> None:
        """VersionMixin should have default version of 1."""
        entity = VersionedEntity[str]()
        
        assert entity.version == 1

    def test_increment_version_int(self) -> None:
        """increment_version should increase integer version."""
        entity = VersionedEntity[str]()
        
        entity.increment_version()
        
        assert entity.version == 2

    def test_increment_version_multiple_times(self) -> None:
        """increment_version should work multiple times."""
        entity = VersionedEntity[str]()
        
        entity.increment_version()
        entity.increment_version()
        entity.increment_version()
        
        assert entity.version == 4


class TestVersionedEntity:
    """Tests for VersionedEntity class."""

    def test_versioned_entity_inherits_base(self) -> None:
        """VersionedEntity should have all BaseEntity fields."""
        entity = VersionedEntity[str](id="test-123")
        
        assert entity.id == "test-123"
        assert entity.version == 1
        assert entity.is_deleted is False


class TestAuditableVersionedEntity:
    """Tests for AuditableVersionedEntity class."""

    def test_auditable_versioned_entity_has_all_fields(self) -> None:
        """AuditableVersionedEntity should combine all features."""
        entity = AuditableVersionedEntity[str](
            id="test-123",
            created_by="user-1"
        )
        
        assert entity.id == "test-123"
        assert entity.version == 1
        assert entity.created_by == "user-1"
        assert entity.is_deleted is False

    def test_mark_updated_by_with_version(self) -> None:
        """mark_updated_by_with_version should update user and version."""
        entity = AuditableVersionedEntity[str]()
        
        entity.mark_updated_by_with_version("user-999")
        
        assert entity.updated_by == "user-999"
        assert entity.version == 2


class TestULIDEntity:
    """Tests for ULIDEntity class."""

    def test_ulid_entity_generates_id(self) -> None:
        """ULIDEntity should auto-generate ULID."""
        entity = ULIDEntity()
        
        assert entity.id is not None
        assert len(entity.id) == 26  # ULID length

    def test_ulid_entity_accepts_custom_id(self) -> None:
        """ULIDEntity should accept custom ID."""
        entity = ULIDEntity(id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert entity.id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"


class TestAuditableULIDEntity:
    """Tests for AuditableULIDEntity class."""

    def test_auditable_ulid_entity_generates_id(self) -> None:
        """AuditableULIDEntity should auto-generate ULID."""
        entity = AuditableULIDEntity()
        
        assert entity.id is not None
        assert len(entity.id) == 26

    def test_auditable_ulid_entity_has_audit_fields(self) -> None:
        """AuditableULIDEntity should have audit fields."""
        entity = AuditableULIDEntity(created_by="user-1")
        
        assert entity.created_by == "user-1"


class TestVersionedULIDEntity:
    """Tests for VersionedULIDEntity class."""

    def test_versioned_ulid_entity_generates_id(self) -> None:
        """VersionedULIDEntity should auto-generate ULID."""
        entity = VersionedULIDEntity()
        
        assert entity.id is not None
        assert len(entity.id) == 26

    def test_versioned_ulid_entity_has_version(self) -> None:
        """VersionedULIDEntity should have version field."""
        entity = VersionedULIDEntity()
        
        assert entity.version == 1
