"""Tests for core/base/domain/entity.py - Base entity classes."""

from datetime import datetime

from src.core.base.domain.entity import (
    AuditableEntity,
    AuditableULIDEntity,
    AuditableVersionedEntity,
    BaseEntity,
    ULIDEntity,
    VersionedEntity,
    VersionedULIDEntity,
)


class TestBaseEntity:
    """Tests for BaseEntity class."""

    def test_default_id_is_none(self):
        entity = BaseEntity()
        assert entity.id is None

    def test_created_at_is_set(self):
        entity = BaseEntity()
        assert entity.created_at is not None
        assert isinstance(entity.created_at, datetime)

    def test_updated_at_is_set(self):
        entity = BaseEntity()
        assert entity.updated_at is not None
        assert isinstance(entity.updated_at, datetime)

    def test_is_deleted_default_false(self):
        entity = BaseEntity()
        assert entity.is_deleted is False

    def test_custom_id(self):
        entity = BaseEntity(id="custom-123")
        assert entity.id == "custom-123"

    def test_mark_updated_changes_timestamp(self):
        entity = BaseEntity()
        original = entity.updated_at
        entity.mark_updated()
        assert entity.updated_at >= original

    def test_mark_deleted_sets_flag(self):
        entity = BaseEntity()
        entity.mark_deleted()
        assert entity.is_deleted is True

    def test_mark_deleted_updates_timestamp(self):
        entity = BaseEntity()
        original = entity.updated_at
        entity.mark_deleted()
        assert entity.updated_at >= original

    def test_mark_restored_clears_flag(self):
        entity = BaseEntity()
        entity.mark_deleted()
        entity.mark_restored()
        assert entity.is_deleted is False

    def test_mark_restored_updates_timestamp(self):
        entity = BaseEntity()
        entity.mark_deleted()
        original = entity.updated_at
        entity.mark_restored()
        assert entity.updated_at >= original


class TestAuditableEntity:
    """Tests for AuditableEntity class."""

    def test_created_by_default_none(self):
        entity = AuditableEntity()
        assert entity.created_by is None

    def test_updated_by_default_none(self):
        entity = AuditableEntity()
        assert entity.updated_by is None

    def test_custom_created_by(self):
        entity = AuditableEntity(created_by="user-123")
        assert entity.created_by == "user-123"

    def test_custom_updated_by(self):
        entity = AuditableEntity(updated_by="user-456")
        assert entity.updated_by == "user-456"

    def test_mark_updated_by_sets_user(self):
        entity = AuditableEntity()
        entity.mark_updated_by("user-789")
        assert entity.updated_by == "user-789"

    def test_mark_updated_by_updates_timestamp(self):
        entity = AuditableEntity()
        original = entity.updated_at
        entity.mark_updated_by("user-789")
        assert entity.updated_at >= original

    def test_inherits_base_entity_fields(self):
        entity = AuditableEntity(id="test-id")
        assert entity.id == "test-id"
        assert entity.is_deleted is False


class TestVersionMixin:
    """Tests for VersionMixin class."""

    def test_version_default_is_one(self):
        entity = VersionedEntity()
        assert entity.version == 1

    def test_increment_version_increases_by_one(self):
        entity = VersionedEntity()
        entity.increment_version()
        assert entity.version == 2

    def test_increment_version_multiple_times(self):
        entity = VersionedEntity()
        entity.increment_version()
        entity.increment_version()
        entity.increment_version()
        assert entity.version == 4


class TestVersionedEntity:
    """Tests for VersionedEntity class."""

    def test_has_version_field(self):
        entity = VersionedEntity()
        assert hasattr(entity, "version")

    def test_inherits_base_entity_fields(self):
        entity = VersionedEntity(id="versioned-id")
        assert entity.id == "versioned-id"
        assert entity.is_deleted is False

    def test_custom_version(self):
        entity = VersionedEntity(version=5)
        assert entity.version == 5


class TestAuditableVersionedEntity:
    """Tests for AuditableVersionedEntity class."""

    def test_has_all_fields(self):
        entity = AuditableVersionedEntity()
        assert hasattr(entity, "id")
        assert hasattr(entity, "created_at")
        assert hasattr(entity, "updated_at")
        assert hasattr(entity, "is_deleted")
        assert hasattr(entity, "created_by")
        assert hasattr(entity, "updated_by")
        assert hasattr(entity, "version")

    def test_mark_updated_by_with_version(self):
        entity = AuditableVersionedEntity()
        entity.mark_updated_by_with_version("user-123")
        assert entity.updated_by == "user-123"
        assert entity.version == 2

    def test_mark_updated_by_with_version_increments(self):
        entity = AuditableVersionedEntity()
        entity.mark_updated_by_with_version("user-1")
        entity.mark_updated_by_with_version("user-2")
        assert entity.version == 3
        assert entity.updated_by == "user-2"


class TestULIDEntity:
    """Tests for ULIDEntity class."""

    def test_auto_generates_ulid(self):
        entity = ULIDEntity()
        assert entity.id is not None
        assert len(entity.id) == 26

    def test_unique_ulids(self):
        entity1 = ULIDEntity()
        entity2 = ULIDEntity()
        assert entity1.id != entity2.id

    def test_inherits_base_entity_fields(self):
        entity = ULIDEntity()
        assert entity.is_deleted is False
        assert entity.created_at is not None


class TestAuditableULIDEntity:
    """Tests for AuditableULIDEntity class."""

    def test_auto_generates_ulid(self):
        entity = AuditableULIDEntity()
        assert entity.id is not None
        assert len(entity.id) == 26

    def test_has_audit_fields(self):
        entity = AuditableULIDEntity(created_by="user-123")
        assert entity.created_by == "user-123"
        assert entity.updated_by is None


class TestVersionedULIDEntity:
    """Tests for VersionedULIDEntity class."""

    def test_auto_generates_ulid(self):
        entity = VersionedULIDEntity()
        assert entity.id is not None
        assert len(entity.id) == 26

    def test_has_version_field(self):
        entity = VersionedULIDEntity()
        assert entity.version == 1

    def test_increment_version(self):
        entity = VersionedULIDEntity()
        entity.increment_version()
        assert entity.version == 2


class TestEntityModelConfig:
    """Tests for entity model configuration."""

    def test_from_attributes_enabled(self):
        assert BaseEntity.model_config.get("from_attributes") is True

    def test_entity_can_be_created_from_dict(self):
        data = {"id": "test-id", "is_deleted": False}
        entity = BaseEntity.model_validate(data)
        assert entity.id == "test-id"
