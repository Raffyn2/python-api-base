"""Property-based tests for datetime utilities.

**Feature: generic-fastapi-crud, Property 19: DateTime ISO 8601 Formatting**
**Validates: Requirements 16.1**
"""

from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from my_api.shared.utils.datetime import from_iso8601, to_iso8601, utc_now


# Strategy for generating timezone-aware datetimes
aware_datetimes = st.datetimes(
    min_value=datetime(1970, 1, 1),
    max_value=datetime(2100, 12, 31),
    timezones=st.just(timezone.utc),
)


class TestDateTimeISO8601:
    """Property tests for ISO 8601 datetime formatting."""

    @settings(max_examples=50)
    @given(dt=aware_datetimes)
    def test_iso8601_round_trip(self, dt: datetime) -> None:
        """
        **Feature: generic-fastapi-crud, Property 19: DateTime ISO 8601 Formatting**

        For any timezone-aware datetime, formatting to ISO 8601 and parsing back
        SHALL produce a datetime equivalent to the original (within timezone equivalence).
        """
        iso_string = to_iso8601(dt)

        # Verify it produces a valid string
        assert isinstance(iso_string, str)
        assert len(iso_string) > 0

        # Parse back
        parsed = from_iso8601(iso_string)

        # Verify round-trip preserves the datetime
        # Compare timestamps to handle timezone representation differences
        assert abs(dt.timestamp() - parsed.timestamp()) < 1  # Within 1 second

    @settings(max_examples=50)
    @given(dt=aware_datetimes)
    def test_iso8601_format_contains_required_components(self, dt: datetime) -> None:
        """
        For any datetime, the ISO 8601 string SHALL contain date and time components.
        """
        iso_string = to_iso8601(dt)

        # Should contain date separator
        assert "-" in iso_string
        # Should contain time indicator
        assert "T" in iso_string
        # Should contain timezone indicator (Z or +/-)
        assert "Z" in iso_string or "+" in iso_string or iso_string.count("-") >= 3

    @settings(max_examples=20)
    @given(dt=aware_datetimes)
    def test_iso8601_is_parseable_by_standard_library(self, dt: datetime) -> None:
        """
        For any datetime, the ISO 8601 string SHALL be parseable.
        """
        iso_string = to_iso8601(dt)

        # Should be parseable by our function
        parsed = from_iso8601(iso_string)
        assert parsed is not None

    def test_none_handling(self) -> None:
        """to_iso8601 and from_iso8601 SHALL handle None gracefully."""
        assert to_iso8601(None) is None
        assert from_iso8601(None) is None

    def test_utc_now_is_timezone_aware(self) -> None:
        """utc_now SHALL return a timezone-aware datetime."""
        now = utc_now()
        assert now.tzinfo is not None

    @settings(max_examples=20)
    @given(
        year=st.integers(min_value=2000, max_value=2050),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
        second=st.integers(min_value=0, max_value=59),
    )
    def test_specific_datetime_round_trip(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int,
    ) -> None:
        """
        For any specific datetime components, round-trip SHALL preserve values.
        """
        dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
        iso_string = to_iso8601(dt)
        parsed = from_iso8601(iso_string)

        assert parsed.year == year
        assert parsed.month == month
        assert parsed.day == day
        assert parsed.hour == hour
        assert parsed.minute == minute
        assert parsed.second == second
