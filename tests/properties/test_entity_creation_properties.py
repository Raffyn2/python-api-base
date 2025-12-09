"""Property-based tests for entity creation.

**Feature: test-coverage-90-percent, Property 2: Entity Creation Consistency**
**Validates: Requirements 2.4, 2.5**
"""

from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from core.base.domain.entity import (
    AuditableEntity,
    BaseEntity,
    ULIDEntity,
    VersionedEntity,
)
from core.base.domain.value_object import EntityId, UserId


# Strategies for entity data
valid_string_id = st.text(
    alphabet=st.sampled_from("0123456789ABCDEFGHJKMNPQRSTVWXYZ"),
    min_size=26,
    max_size=26
)

valid_int_id = st.integers(min_value=1, max_value=1000000)

valid_user_id = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())

valid_version = st.integers(min_value=1, max_value=1000)


class TestEntityCreationProperties:
    """Property-based tests for entity creation.
    
    **Feature: test-coverage-90-percent, Property 2: Entity Creation Consistency**
    **Validates: Requirements 2.4, 2.5**
    """

    @given(entity_id=valid_string_id)
    @settings(max_examples=100)
    def test_base_entity_preserves_string_id(self, entity_id: str) -> None:
        """Entity should preserve provided string ID.
        
        *For any* valid string ID, creating an entity should result in 
        the ID being correctly set.
        """
        entity = BaseEntity[str](id=entity_id)
        
        assert entity.id == entity_id

    @given(entity_id=valid_int_id)
    @settings(max_examples=100)
    def test_base_entity_preserves_int_id(self, entity_id: int) -> None:
        """Entity should preserve provided integer ID.
        
        *For any* valid integer ID, creating an entity should result in 
        the ID being correctly set.
        """
        entity = BaseEntity[int](id=entity_id)
        
        assert entity.id == entity_id

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_entity_has_timestamps(self, _: int) -> None:
        """Entity should always have timestamps set.
        
        *For any* created entity, timestamps should be set.
        """
        entity = BaseEntity[str]()
        
        assert entity.created_at is not None
        assert entity.updated_at is not None
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_entity_not_deleted_by_default(self, _: int) -> None:
        """Entity should not be deleted by default.
        
        *For any* created entity, is_deleted should be False.
        """
        entity = BaseEntity[str]()
        
        assert entity.is_deleted is False

    @given(
        created_by=valid_user_id,
        updated_by=valid_user_id
    )
    @settings(max_examples=100)
    def test_auditable_entity_preserves_audit_fields(
        self, created_by: str, updated_by: str
    ) -> None:
        """AuditableEntity should preserve audit fields.
        
        *For any* valid audit data, creating an entity should preserve it.
        """
        entity = AuditableEntity[str](
            created_by=created_by,
            updated_by=updated_by
        )
        
        assert entity.created_by == created_by
        assert entity.updated_by == updated_by

    @given(version=valid_version)
    @settings(max_examples=100)
    def test_versioned_entity_preserves_version(self, version: int) -> None:
        """VersionedEntity should preserve version.
        
        *For any* valid version, creating an entity should preserve it.
        """
        entity = VersionedEntity[str](version=version)
        
        assert entity.version == version

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_versioned_entity_default_version(self, _: int) -> None:
        """VersionedEntity should have default version of 1.
        
        *For any* created versioned entity without version, version should be 1.
        """
        entity = VersionedEntity[str]()
        
        assert entity.version == 1

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_ulid_entity_generates_valid_id(self, _: int) -> None:
        """ULIDEntity should generate valid ULID.
        
        *For any* created ULID entity, ID should be valid ULID format.
        """
        entity = ULIDEntity()
        
        assert entity.id is not None
        assert len(entity.id) == 26

    @given(count=st.integers(min_value=2, max_value=50))
    @settings(max_examples=30)
    def test_ulid_entity_unique_ids(self, count: int) -> None:
        """ULIDEntity should generate unique IDs.
        
        *For any* batch of ULID entities, all IDs should be unique.
        """
        entities = [ULIDEntity() for _ in range(count)]
        ids = [e.id for e in entities]
        unique_ids = set(ids)
        
        assert len(unique_ids) == count

    @given(entity_id=valid_string_id, is_deleted=st.booleans())
    @settings(max_examples=100)
    def test_entity_preserves_deleted_flag(
        self, entity_id: str, is_deleted: bool
    ) -> None:
        """Entity should preserve is_deleted flag.
        
        *For any* valid entity data, is_deleted should be preserved.
        """
        entity = BaseEntity[str](id=entity_id, is_deleted=is_deleted)
        
        assert entity.is_deleted == is_deleted


class TestEntityIdValueObjectProperties:
    """Property-based tests for EntityId value object.
    
    **Feature: test-coverage-90-percent, Property 2: Entity Creation Consistency**
    **Validates: Requirements 2.4, 2.5**
    """

    @given(ulid=valid_string_id)
    @settings(max_examples=100)
    def test_entity_id_preserves_value(self, ulid: str) -> None:
        """EntityId should preserve ULID value (uppercase).
        
        *For any* valid ULID, EntityId should store it uppercase.
        """
        entity_id = EntityId(ulid)
        
        assert entity_id.value == ulid.upper()

    @given(ulid=valid_string_id)
    @settings(max_examples=100)
    def test_entity_id_equality(self, ulid: str) -> None:
        """EntityIds with same value should be equal.
        
        *For any* valid ULID, two EntityIds with same value should be equal.
        """
        id1 = EntityId(ulid)
        id2 = EntityId(ulid)
        
        assert id1 == id2

    @given(ulid=valid_string_id)
    @settings(max_examples=100)
    def test_entity_id_hash_consistency(self, ulid: str) -> None:
        """EntityIds with same value should have same hash.
        
        *For any* valid ULID, hash should be consistent.
        """
        id1 = EntityId(ulid)
        id2 = EntityId(ulid)
        
        assert hash(id1) == hash(id2)

    @given(ulid=valid_string_id)
    @settings(max_examples=100)
    def test_entity_id_str_representation(self, ulid: str) -> None:
        """EntityId str should return value.
        
        *For any* valid ULID, str(EntityId) should return the value.
        """
        entity_id = EntityId(ulid)
        
        assert str(entity_id) == ulid.upper()

    @given(ulid=valid_string_id)
    @settings(max_examples=100)
    def test_user_id_preserves_value(self, ulid: str) -> None:
        """UserId should preserve ULID value.
        
        *For any* valid ULID, UserId should store it correctly.
        """
        user_id = UserId(ulid)
        
        assert user_id.value == ulid.upper()


class TestInvalidEntityCreationProperties:
    """Property-based tests for invalid entity creation.
    
    **Feature: test-coverage-90-percent, Property 2: Entity Creation Consistency**
    **Validates: Requirements 2.5**
    """

    @given(invalid_ulid=st.text(min_size=1, max_size=25))
    @settings(max_examples=50)
    def test_entity_id_rejects_short_ulid(self, invalid_ulid: str) -> None:
        """EntityId should reject ULIDs that are too short.
        
        *For any* string shorter than 26 chars, EntityId should raise error.
        """
        try:
            EntityId(invalid_ulid)
            # If it doesn't raise, the ULID was somehow valid (unlikely)
            assert len(invalid_ulid) == 26
        except ValueError:
            pass  # Expected

    @given(invalid_ulid=st.text(min_size=27, max_size=50))
    @settings(max_examples=50)
    def test_entity_id_rejects_long_ulid(self, invalid_ulid: str) -> None:
        """EntityId should reject ULIDs that are too long.
        
        *For any* string longer than 26 chars, EntityId should raise error.
        """
        try:
            EntityId(invalid_ulid)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_entity_id_rejects_empty(self, _: int) -> None:
        """EntityId should reject empty string.
        
        *For any* attempt to create EntityId with empty string, should raise.
        """
        try:
            EntityId("")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "empty" in str(e).lower()
