"""Property-based tests for structured logging.

**Feature: structured-logging-standardization**
"""

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from core.structured_logging.structured import (
    JSONLogFormatter,
    StructuredLogEntry,
    create_log_entry,
)

# =============================================================================
# Strategies for generating test data
# =============================================================================

valid_levels = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

# Non-empty strings for messages and operations
non_empty_text = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())

# Valid identifier keys for extra fields
valid_keys = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=20,
).filter(lambda s: s and s[0].isalpha())

# JSON-serializable values
json_values = st.one_of(
    st.integers(min_value=-1_000_000, max_value=1_000_000),
    st.text(max_size=100),
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
)

# Extra fields dictionary (always includes operation)
extra_fields = st.dictionaries(
    keys=valid_keys,
    values=json_values,
    max_size=10,
)


# =============================================================================
# Property Tests
# =============================================================================


class TestStructuredLogEntryProperties:
    """Property-based tests for StructuredLogEntry."""

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        message=non_empty_text,
        level=valid_levels,
        operation=non_empty_text,
        additional_fields=extra_fields,
    )
    def test_operation_field_presence(
        self,
        message: str,
        level: str,
        operation: str,
        additional_fields: dict,
    ) -> None:
        """
        **Feature: structured-logging-standardization, Property 1: Operation Field Presence**
        **Validates: Requirements 1.4**

        For any structured log entry emitted by the system, the extra dictionary
        SHALL contain an operation field with a non-empty string value.
        """
        # Ensure operation is not overwritten by additional_fields
        extra = {"operation": operation, **additional_fields}
        extra["operation"] = operation  # Guarantee operation is set

        entry = StructuredLogEntry(
            message=message,
            level=level,
            extra=extra,
        )

        # Property: operation field must exist and be non-empty
        assert "operation" in entry.extra
        assert entry.extra["operation"]
        assert isinstance(entry.extra["operation"], str)

    @settings(max_examples=100)
    @given(
        message=non_empty_text,
        level=valid_levels,
        operation=non_empty_text,
        additional_fields=extra_fields,
    )
    def test_log_entry_round_trip(
        self,
        message: str,
        level: str,
        operation: str,
        additional_fields: dict,
    ) -> None:
        """
        **Feature: structured-logging-standardization, Property 2: Log Entry Round-Trip Consistency**
        **Validates: Requirements 8.1, 8.2, 8.3**

        For any valid StructuredLogEntry, formatting to string and parsing back
        SHALL produce an equivalent entry with identical message, level, timestamp,
        and extra fields.
        """
        extra = {"operation": operation, **additional_fields}
        extra["operation"] = operation

        original = StructuredLogEntry(
            message=message,
            level=level,
            extra=extra,
        )

        formatter = JSONLogFormatter()

        # Round-trip: format then parse
        formatted = formatter.format(original)
        parsed = formatter.parse(formatted)

        # Property: round-trip preserves all fields
        assert parsed.message == original.message
        assert parsed.level == original.level
        assert parsed.timestamp == original.timestamp
        assert parsed.extra == original.extra


class TestStructuredLogEntryValidation:
    """Unit tests for StructuredLogEntry validation."""

    def test_missing_operation_raises_error(self) -> None:
        """Entry without operation field should raise ValueError."""
        with pytest.raises(ValueError, match="operation"):
            StructuredLogEntry(
                message="Test message",
                level="INFO",
                extra={},
            )

    def test_empty_operation_raises_error(self) -> None:
        """Entry with empty operation should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            StructuredLogEntry(
                message="Test message",
                level="INFO",
                extra={"operation": ""},
            )

    def test_empty_message_raises_error(self) -> None:
        """Entry with empty message should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            StructuredLogEntry(
                message="",
                level="INFO",
                extra={"operation": "TEST"},
            )

    def test_invalid_level_raises_error(self) -> None:
        """Entry with invalid level should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            StructuredLogEntry(
                message="Test",
                level="INVALID",
                extra={"operation": "TEST"},
            )

    def test_valid_entry_creation(self) -> None:
        """Valid entry should be created successfully."""
        entry = StructuredLogEntry(
            message="Test message",
            level="INFO",
            extra={"operation": "TEST_OP", "user_id": "123"},
        )

        assert entry.message == "Test message"
        assert entry.level == "INFO"
        assert entry.extra["operation"] == "TEST_OP"
        assert entry.extra["user_id"] == "123"


class TestJSONLogFormatter:
    """Unit tests for JSONLogFormatter."""

    def test_format_produces_valid_json(self) -> None:
        """Format should produce valid JSON string."""
        import json

        entry = StructuredLogEntry(
            message="Test",
            level="INFO",
            extra={"operation": "TEST"},
        )
        formatter = JSONLogFormatter()

        result = formatter.format(entry)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["message"] == "Test"
        assert parsed["level"] == "INFO"

    def test_parse_invalid_json_raises_error(self) -> None:
        """Parse should raise ValueError for invalid JSON."""
        formatter = JSONLogFormatter()

        with pytest.raises(ValueError, match="Failed to parse"):
            formatter.parse("not valid json")

    def test_parse_missing_fields_raises_error(self) -> None:
        """Parse should raise ValueError for missing required fields."""
        formatter = JSONLogFormatter()

        with pytest.raises(ValueError):
            formatter.parse('{"message": "test"}')

    def test_non_serializable_values_converted_to_string(self) -> None:
        """Non-JSON-serializable values should be converted to strings."""
        import json
        from datetime import datetime

        entry = StructuredLogEntry(
            message="Test",
            level="INFO",
            extra={"operation": "TEST", "timestamp": datetime(2025, 1, 1)},
        )
        formatter = JSONLogFormatter()

        result = formatter.format(entry)
        parsed = json.loads(result)

        # datetime should be converted to string
        assert isinstance(parsed["extra"]["timestamp"], str)


class TestCreateLogEntry:
    """Unit tests for create_log_entry factory function."""

    def test_creates_entry_with_operation(self) -> None:
        """Factory should create entry with operation in extra."""
        entry = create_log_entry(
            "Test message",
            "INFO",
            "TEST_OPERATION",
            user_id="123",
        )

        assert entry.message == "Test message"
        assert entry.level == "INFO"
        assert entry.extra["operation"] == "TEST_OPERATION"
        assert entry.extra["user_id"] == "123"
