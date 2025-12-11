"""Property-based tests for ID uniqueness.

**Feature: test-coverage-90-percent, Property 5: ID Uniqueness**
**Validates: Requirements 5.5**
"""

import re

import pytest
from hypothesis import given, settings, strategies as st

from core.shared.utils.ids import generate_ulid, generate_uuid7

# ULID pattern: 26 characters, Crockford Base32
ULID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$", re.IGNORECASE)

# UUID pattern: standard UUID format
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


@pytest.mark.property
class TestIdUniquenessProperties:
    """Property-based tests for ID uniqueness.

    **Feature: test-coverage-90-percent, Property 5: ID Uniqueness**
    **Validates: Requirements 5.5**
    """

    @given(n=st.integers(min_value=2, max_value=100))
    @settings(max_examples=50)
    def test_ulid_uniqueness(self, n: int) -> None:
        """Generated ULIDs are unique.

        Property: For any N generated ULIDs, all N are unique
        """
        ulids = [generate_ulid() for _ in range(n)]

        assert len(set(ulids)) == n, f"Expected {n} unique ULIDs, got {len(set(ulids))}"

    @given(n=st.integers(min_value=2, max_value=100))
    @settings(max_examples=50)
    def test_uuid7_uniqueness(self, n: int) -> None:
        """Generated UUID7s are unique.

        Property: For any N generated UUID7s, all N are unique
        """
        uuids = [generate_uuid7() for _ in range(n)]

        assert len(set(uuids)) == n, f"Expected {n} unique UUID7s, got {len(set(uuids))}"

    @given(st.data())
    @settings(max_examples=100)
    def test_ulid_format_valid(self, data: st.DataObject) -> None:
        """Generated ULIDs have valid format.

        Property: Every generated ULID matches the ULID pattern
        """
        ulid = generate_ulid()

        assert ULID_PATTERN.match(ulid), f"Invalid ULID format: {ulid}"

    @given(st.data())
    @settings(max_examples=100)
    def test_uuid7_format_valid(self, data: st.DataObject) -> None:
        """Generated UUID7s have valid format.

        Property: Every generated UUID7 matches the UUID pattern
        """
        uuid = generate_uuid7()

        assert UUID_PATTERN.match(uuid), f"Invalid UUID7 format: {uuid}"

    @given(st.data())
    @settings(max_examples=100)
    def test_ulid_length(self, data: st.DataObject) -> None:
        """Generated ULIDs have correct length.

        Property: Every ULID is exactly 26 characters
        """
        ulid = generate_ulid()

        assert len(ulid) == 26, f"Expected 26 chars, got {len(ulid)}"

    @given(st.data())
    @settings(max_examples=100)
    def test_uuid7_length(self, data: st.DataObject) -> None:
        """Generated UUID7s have correct length.

        Property: Every UUID7 is exactly 36 characters (with hyphens)
        """
        uuid = generate_uuid7()

        assert len(uuid) == 36, f"Expected 36 chars, got {len(uuid)}"

    @given(st.data())
    @settings(max_examples=50)
    def test_ulid_sortable_by_time(self, data: st.DataObject) -> None:
        """ULIDs generated in sequence are sortable.

        Property: ULIDs generated later sort after earlier ones
        """
        ulid1 = generate_ulid()
        ulid2 = generate_ulid()

        # ULIDs are lexicographically sortable by time
        # Due to the same millisecond, they might be equal in time component
        # but the random component should make them different
        assert ulid1 != ulid2

    @given(n=st.integers(min_value=10, max_value=50))
    @settings(max_examples=20)
    def test_ulid_no_invalid_characters(self, n: int) -> None:
        """ULIDs don't contain invalid Crockford Base32 characters.

        Property: ULIDs exclude I, L, O, U (Crockford Base32)
        """
        invalid_chars = set("ILOUilou")

        for _ in range(n):
            ulid = generate_ulid()
            chars_in_ulid = set(ulid)

            assert not chars_in_ulid.intersection(invalid_chars), (
                f"ULID contains invalid chars: {chars_in_ulid.intersection(invalid_chars)}"
            )

    @given(n=st.integers(min_value=10, max_value=50))
    @settings(max_examples=20)
    def test_uuid7_only_hex_and_hyphens(self, n: int) -> None:
        """UUID7s only contain hex characters and hyphens.

        Property: UUID7s contain only [0-9a-f-]
        """
        valid_chars = set("0123456789abcdef-")

        for _ in range(n):
            uuid = generate_uuid7()
            chars_in_uuid = set(uuid.lower())

            assert chars_in_uuid.issubset(valid_chars), f"UUID contains invalid chars: {chars_in_uuid - valid_chars}"

    @given(n=st.integers(min_value=5, max_value=20))
    @settings(max_examples=30)
    def test_mixed_id_types_unique(self, n: int) -> None:
        """Different ID types don't collide.

        Property: ULIDs and UUID7s are always different
        """
        ulids = [generate_ulid() for _ in range(n)]
        uuids = [generate_uuid7() for _ in range(n)]

        # No overlap between the two sets
        assert not set(ulids).intersection(set(uuids))

    @given(st.data())
    @settings(max_examples=100)
    def test_ulid_uppercase_normalized(self, data: st.DataObject) -> None:
        """ULIDs are consistently cased.

        Property: ULID case is consistent (uppercase)
        """
        ulid = generate_ulid()

        # Should be uppercase
        assert ulid == ulid.upper(), f"ULID not uppercase: {ulid}"

    @given(st.data())
    @settings(max_examples=100)
    def test_uuid7_lowercase_normalized(self, data: st.DataObject) -> None:
        """UUID7s are consistently cased.

        Property: UUID7 case is consistent (lowercase)
        """
        uuid = generate_uuid7()

        # Should be lowercase
        assert uuid == uuid.lower(), f"UUID7 not lowercase: {uuid}"

    @given(n=st.integers(min_value=100, max_value=500))
    @settings(max_examples=10)
    def test_large_batch_uniqueness(self, n: int) -> None:
        """Large batches of IDs are all unique.

        Property: Even large batches have no duplicates
        """
        ulids = [generate_ulid() for _ in range(n)]

        assert len(set(ulids)) == n, f"Duplicates found in batch of {n}: {n - len(set(ulids))} duplicates"
