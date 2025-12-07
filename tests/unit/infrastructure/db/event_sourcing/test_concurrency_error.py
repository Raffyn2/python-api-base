"""Tests for infrastructure/db/event_sourcing/exceptions.py - Event sourcing exceptions."""

import pytest

from src.infrastructure.db.event_sourcing.exceptions import ConcurrencyError


class TestConcurrencyError:
    """Tests for ConcurrencyError class."""

    def test_basic_message(self):
        error = ConcurrencyError("Concurrency conflict")
        assert str(error) == "Concurrency conflict"

    def test_message_with_versions(self):
        error = ConcurrencyError(
            "Concurrency conflict",
            expected_version=5,
            actual_version=7,
        )
        assert "expected: 5" in str(error)
        assert "actual: 7" in str(error)

    def test_expected_version_attribute(self):
        error = ConcurrencyError("Error", expected_version=3, actual_version=5)
        assert error.expected_version == 3

    def test_actual_version_attribute(self):
        error = ConcurrencyError("Error", expected_version=3, actual_version=5)
        assert error.actual_version == 5

    def test_versions_default_none(self):
        error = ConcurrencyError("Error")
        assert error.expected_version is None
        assert error.actual_version is None

    def test_is_exception(self):
        error = ConcurrencyError("Error")
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        with pytest.raises(ConcurrencyError) as exc_info:
            raise ConcurrencyError("Test error", expected_version=1, actual_version=2)
        assert exc_info.value.expected_version == 1
        assert exc_info.value.actual_version == 2

    def test_only_expected_version(self):
        error = ConcurrencyError("Error", expected_version=5)
        assert error.expected_version == 5
        assert error.actual_version is None
        # Message should not include version info if both not provided
        assert "expected: 5" not in str(error)

    def test_only_actual_version(self):
        error = ConcurrencyError("Error", actual_version=7)
        assert error.expected_version is None
        assert error.actual_version == 7
        # Message should not include version info if both not provided
        assert "actual: 7" not in str(error)

    def test_message_format(self):
        error = ConcurrencyError(
            "Aggregate version mismatch",
            expected_version=10,
            actual_version=12,
        )
        expected_msg = "Aggregate version mismatch (expected: 10, actual: 12)"
        assert str(error) == expected_msg
