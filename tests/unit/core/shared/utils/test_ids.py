"""Tests for ID generation utilities."""

from datetime import UTC, datetime

import pytest

from core.shared.utils.ids import (
    compare_ulids,
    generate_ulid,
    generate_uuid7,
    is_valid_ulid,
    is_valid_uuid7,
    ulid_from_datetime,
    ulid_to_datetime,
)


class TestGenerateUlid:
    """Tests for generate_ulid function."""

    def test_returns_string(self) -> None:
        result = generate_ulid()
        assert isinstance(result, str)

    def test_returns_26_characters(self) -> None:
        result = generate_ulid()
        assert len(result) == 26

    def test_generates_unique_ids(self) -> None:
        ids = [generate_ulid() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_ids_are_sortable(self) -> None:
        ids = [generate_ulid() for _ in range(10)]
        sorted_ids = sorted(ids)
        # Later generated IDs should sort after earlier ones
        assert sorted_ids == ids


class TestGenerateUuid7:
    """Tests for generate_uuid7 function."""

    def test_returns_string(self) -> None:
        result = generate_uuid7()
        assert isinstance(result, str)

    def test_returns_36_characters(self) -> None:
        result = generate_uuid7()
        assert len(result) == 36

    def test_has_uuid_format(self) -> None:
        result = generate_uuid7()
        parts = result.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_generates_unique_ids(self) -> None:
        ids = [generate_uuid7() for _ in range(100)]
        assert len(set(ids)) == 100


class TestUlidFromDatetime:
    """Tests for ulid_from_datetime function."""

    def test_creates_ulid_from_datetime(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = ulid_from_datetime(dt)
        assert isinstance(result, str)
        assert len(result) == 26

    def test_preserves_timestamp(self) -> None:
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        ulid = ulid_from_datetime(dt)
        extracted = ulid_to_datetime(ulid)
        # ULID has millisecond precision
        assert abs((extracted - dt).total_seconds()) < 0.001


class TestUlidToDatetime:
    """Tests for ulid_to_datetime function."""

    def test_extracts_datetime(self) -> None:
        ulid = generate_ulid()
        result = ulid_to_datetime(ulid)
        assert isinstance(result, datetime)

    def test_datetime_is_recent(self) -> None:
        ulid = generate_ulid()
        result = ulid_to_datetime(ulid)
        now = datetime.now(UTC)
        # Should be within last second
        assert abs((now - result).total_seconds()) < 1


class TestIsValidUlid:
    """Tests for is_valid_ulid function."""

    def test_valid_ulid(self) -> None:
        ulid = generate_ulid()
        assert is_valid_ulid(ulid) is True

    def test_invalid_empty(self) -> None:
        assert is_valid_ulid("") is False

    def test_invalid_too_short(self) -> None:
        assert is_valid_ulid("01ARZ3NDEKTSV4RRFFQ69G5FA") is False  # 25 chars

    def test_invalid_too_long(self) -> None:
        assert is_valid_ulid("01ARZ3NDEKTSV4RRFFQ69G5FAAA") is False  # 27 chars

    def test_invalid_characters(self) -> None:
        assert is_valid_ulid("01ARZ3NDEKTSV4RRFFQ69G5FA!") is False

    def test_invalid_none(self) -> None:
        assert is_valid_ulid(None) is False  # type: ignore


class TestIsValidUuid7:
    """Tests for is_valid_uuid7 function."""

    def test_valid_uuid7(self) -> None:
        uuid = generate_uuid7()
        assert is_valid_uuid7(uuid) is True

    def test_invalid_empty(self) -> None:
        assert is_valid_uuid7("") is False

    def test_invalid_too_short(self) -> None:
        assert is_valid_uuid7("12345678-1234-7234-1234-12345678901") is False

    def test_invalid_uuid4(self) -> None:
        # UUID v4 has version 4, not 7
        import uuid
        uuid4 = str(uuid.uuid4())
        assert is_valid_uuid7(uuid4) is False

    def test_invalid_none(self) -> None:
        assert is_valid_uuid7(None) is False  # type: ignore


class TestCompareUlids:
    """Tests for compare_ulids function."""

    def test_equal_ulids(self) -> None:
        ulid = generate_ulid()
        assert compare_ulids(ulid, ulid) == 0

    def test_first_less_than_second(self) -> None:
        ulid1 = generate_ulid()
        ulid2 = generate_ulid()
        # ulid1 was generated first, so it should be less
        assert compare_ulids(ulid1, ulid2) == -1

    def test_first_greater_than_second(self) -> None:
        ulid1 = generate_ulid()
        ulid2 = generate_ulid()
        # ulid2 was generated second, so ulid1 < ulid2
        assert compare_ulids(ulid2, ulid1) == 1

    def test_lexicographic_comparison(self) -> None:
        # ULIDs are lexicographically sortable
        ulid1 = "01ARZ3NDEKTSV4RRFFQ69G5FAA"
        ulid2 = "01ARZ3NDEKTSV4RRFFQ69G5FAB"
        assert compare_ulids(ulid1, ulid2) == -1
        assert compare_ulids(ulid2, ulid1) == 1
