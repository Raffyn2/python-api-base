"""Tests for time utilities."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from core.shared.utils.time import (
    add_duration,
    end_of_day,
    ensure_utc,
    format_datetime,
    from_iso8601,
    from_timestamp,
    now,
    start_of_day,
    to_iso8601,
    to_timestamp,
    utc_now,
)


class TestUtcNow:
    """Tests for utc_now function."""

    def test_returns_datetime(self) -> None:
        result = utc_now()
        assert isinstance(result, datetime)

    def test_has_utc_timezone(self) -> None:
        result = utc_now()
        assert result.tzinfo == UTC

    def test_is_current_time(self) -> None:
        before = datetime.now(UTC)
        result = utc_now()
        after = datetime.now(UTC)
        assert before <= result <= after


class TestNow:
    """Tests for now function."""

    def test_default_is_utc(self) -> None:
        result = now()
        assert result.tzinfo == UTC

    def test_with_custom_timezone(self) -> None:
        eastern = timezone(timedelta(hours=-5))
        result = now(eastern)
        assert result.tzinfo == eastern

    def test_returns_current_time(self) -> None:
        before = datetime.now(UTC)
        result = now()
        after = datetime.now(UTC)
        assert before <= result <= after


class TestToTimestamp:
    """Tests for to_timestamp function."""

    def test_converts_to_float(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = to_timestamp(dt)
        assert isinstance(result, float)

    def test_epoch_is_zero(self) -> None:
        dt = datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = to_timestamp(dt)
        assert result == 0.0

    def test_known_timestamp(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = to_timestamp(dt)
        assert result == 1704067200.0


class TestFromTimestamp:
    """Tests for from_timestamp function."""

    def test_returns_datetime(self) -> None:
        result = from_timestamp(0)
        assert isinstance(result, datetime)

    def test_has_utc_timezone(self) -> None:
        result = from_timestamp(0)
        assert result.tzinfo == UTC

    def test_epoch_conversion(self) -> None:
        result = from_timestamp(0)
        assert result == datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_known_timestamp(self) -> None:
        result = from_timestamp(1704067200.0)
        assert result == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)


class TestToIso8601:
    """Tests for to_iso8601 function."""

    def test_returns_string(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = to_iso8601(dt)
        assert isinstance(result, str)

    def test_format(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = to_iso8601(dt)
        assert "2024-01-15" in result
        assert "10:30:00" in result


class TestFromIso8601:
    """Tests for from_iso8601 function."""

    def test_parses_with_timezone(self) -> None:
        result = from_iso8601("2024-01-15T10:30:00+00:00")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parses_with_z_suffix(self) -> None:
        result = from_iso8601("2024-01-15T10:30:00Z")
        assert result.year == 2024
        assert result.tzinfo is not None

    def test_parses_without_timezone(self) -> None:
        result = from_iso8601("2024-01-15T10:30:00")
        assert result.year == 2024

    def test_roundtrip(self) -> None:
        original = datetime(2024, 6, 15, 12, 30, 45, tzinfo=UTC)
        iso_str = to_iso8601(original)
        parsed = from_iso8601(iso_str)
        assert parsed == original


class TestFormatDatetime:
    """Tests for format_datetime function."""

    def test_default_format(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_datetime(dt)
        assert result == "2024-01-15 10:30:45"

    def test_custom_format(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_datetime(dt, "%d/%m/%Y")
        assert result == "15/01/2024"

    def test_time_only_format(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_datetime(dt, "%H:%M")
        assert result == "10:30"


class TestEnsureUtc:
    """Tests for ensure_utc function."""

    def test_naive_datetime_gets_utc(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = ensure_utc(dt)
        assert result.tzinfo == UTC

    def test_utc_datetime_unchanged(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = ensure_utc(dt)
        assert result == dt

    def test_other_timezone_converted(self) -> None:
        eastern = timezone(timedelta(hours=-5))
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=eastern)
        result = ensure_utc(dt)
        assert result.tzinfo == UTC
        assert result.hour == 15  # 10:30 EST = 15:30 UTC


class TestStartOfDay:
    """Tests for start_of_day function."""

    def test_sets_time_to_midnight(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)
        result = start_of_day(dt)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_preserves_date(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = start_of_day(dt)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_preserves_timezone(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = start_of_day(dt)
        assert result.tzinfo == UTC


class TestEndOfDay:
    """Tests for end_of_day function."""

    def test_sets_time_to_end(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = end_of_day(dt)
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        assert result.microsecond == 999999

    def test_preserves_date(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = end_of_day(dt)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15


class TestAddDuration:
    """Tests for add_duration function."""

    def test_add_days(self) -> None:
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = add_duration(dt, days=5)
        assert result.day == 20

    def test_add_hours(self) -> None:
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = add_duration(dt, hours=3)
        assert result.hour == 13

    def test_add_minutes(self) -> None:
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = add_duration(dt, minutes=30)
        assert result.minute == 30

    def test_add_seconds(self) -> None:
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = add_duration(dt, seconds=45)
        assert result.second == 45

    def test_add_multiple(self) -> None:
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = add_duration(dt, days=1, hours=2, minutes=30, seconds=15)
        assert result.day == 16
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 15

    def test_negative_duration(self) -> None:
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = add_duration(dt, days=-5)
        assert result.day == 10
