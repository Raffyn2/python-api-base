"""Structured logging utilities for consistent observability.

**Feature: structured-logging-standardization**
**Validates: Requirements 1.4, 8.1, 8.2, 8.3**

This module provides:
- StructuredLogEntry: Immutable dataclass for log entries with required operation field
- JSONLogFormatter: Format/parse log entries to/from JSON strings
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class StructuredLogEntry:
    """Immutable log entry with structured data.

    All log entries must include an 'operation' field in extra
    for consistent filtering and observability.

    Attributes:
        message: Static log message without variable interpolation.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        timestamp: ISO 8601 UTC timestamp.
        extra: Dictionary of contextual key-value pairs (must include 'operation').

    Example:
        >>> entry = StructuredLogEntry(
        ...     message="Request processed",
        ...     level="INFO",
        ...     timestamp="2025-01-01T00:00:00Z",
        ...     extra={"operation": "HTTP_REQUEST", "status_code": 200},
        ... )
    """

    message: str
    level: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate that required fields are present."""
        if not self.message:
            msg = "Log entry message cannot be empty"
            raise ValueError(msg)

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            msg = f"Invalid log level: {self.level}. Must be one of {valid_levels}"
            raise ValueError(msg)

        if "operation" not in self.extra:
            msg = "Log entry must include 'operation' field in extra"
            raise ValueError(msg)

        if not self.extra["operation"]:
            msg = "Operation field cannot be empty"
            raise ValueError(msg)


class JSONLogFormatter:
    """Format and parse structured log entries as JSON.

    Provides round-trip consistency: parse(format(entry)) == entry

    Example:
        >>> formatter = JSONLogFormatter()
        >>> entry = StructuredLogEntry(
        ...     message="Test",
        ...     level="INFO",
        ...     extra={"operation": "TEST"},
        ... )
        >>> json_str = formatter.format(entry)
        >>> parsed = formatter.parse(json_str)
        >>> parsed.message == entry.message
        True
    """

    def format(self, entry: StructuredLogEntry) -> str:
        """Format a log entry to JSON string.

        Args:
            entry: The structured log entry to format.

        Returns:
            JSON string representation of the entry.

        Raises:
            ValueError: If entry cannot be serialized.
        """
        try:
            data = {
                "message": entry.message,
                "level": entry.level,
                "timestamp": entry.timestamp,
                "extra": self._serialize_extra(entry.extra),
            }
            return json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            msg = f"Failed to serialize log entry: {e}"
            raise ValueError(msg) from e

    def parse(self, formatted: str) -> StructuredLogEntry:
        """Parse a JSON string back to a log entry.

        Args:
            formatted: JSON string to parse.

        Returns:
            StructuredLogEntry reconstructed from JSON.

        Raises:
            ValueError: If string cannot be parsed or is invalid.
        """
        try:
            data = json.loads(formatted)
            return StructuredLogEntry(
                message=data["message"],
                level=data["level"],
                timestamp=data["timestamp"],
                extra=data["extra"],
            )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            msg = f"Failed to parse log entry: {e}"
            raise ValueError(msg) from e

    def _serialize_extra(self, extra: dict[str, Any]) -> dict[str, Any]:
        """Serialize extra fields, converting non-JSON types to strings.

        Args:
            extra: Dictionary of extra fields.

        Returns:
            Dictionary with all values JSON-serializable.
        """
        result: dict[str, Any] = {}
        for key, value in extra.items():
            try:
                # Test if value is JSON serializable
                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                # Convert to string if not serializable
                result[key] = str(value)
        return result


def create_log_entry(
    message: str,
    level: str,
    operation: str,
    **extra: Any,
) -> StructuredLogEntry:
    """Factory function to create a structured log entry.

    Args:
        message: Static log message.
        level: Log level.
        operation: Operation tag for filtering.
        **extra: Additional contextual fields.

    Returns:
        StructuredLogEntry with all fields populated.

    Example:
        >>> entry = create_log_entry(
        ...     "User logged in",
        ...     "INFO",
        ...     "AUTH_LOGIN",
        ...     user_id="123",
        ... )
    """
    return StructuredLogEntry(
        message=message,
        level=level,
        extra={"operation": operation, **extra},
    )
