"""Mapper error exception.

**Feature: application-layer-code-review-2025**
**Refactored: Split from mapper.py for one-class-per-file compliance**

Note: This is a simplified version for application layer use.
For HTTP/API handlers, use core.errors which includes
correlation_id, timestamp, and RFC 7807 support.
"""

from typing import Any

from application.common.errors.base.application_error import ApplicationError


class MapperError(ApplicationError):
    """Error during mapping operation.

    Raised when entity-to-DTO or DTO-to-entity conversion fails.

    Attributes:
        source_type: Name of the source type being mapped.
        target_type: Name of the target type being mapped to.
        field: Specific field that caused the error (if applicable).
        context: Additional context information.

    Example:
        >>> raise MapperError(
        ...     message="Required field 'name' is missing",
        ...     source_type="UserDTO",
        ...     target_type="UserEntity",
        ...     field="name",
        ... )
    """

    def __init__(
        self,
        message: str,
        source_type: str | None = None,
        target_type: str | None = None,
        field: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize mapper error.

        Args:
            message: Error message describing the mapping failure.
            source_type: Name of the source type being mapped.
            target_type: Name of the target type being mapped to.
            field: Specific field that caused the error.
            context: Additional context information.
        """
        self.source_type = source_type
        self.target_type = target_type
        self.field = field
        self.context = context or {}

        # Build details for ApplicationError
        details: dict[str, Any] = {}
        if source_type:
            details["source_type"] = source_type
        if target_type:
            details["target_type"] = target_type
        if field:
            details["field"] = field
        if self.context:
            details["context"] = self.context

        super().__init__(
            message=message,
            code="MAPPER_ERROR",
            details=details if details else None,
        )

    def __str__(self) -> str:
        """Return formatted error message with mapping context."""
        parts = [self.message]
        if self.source_type and self.target_type:
            parts.append(f"({self.source_type} -> {self.target_type})")
        if self.field:
            parts.append(f"[field: {self.field}]")
        return " ".join(parts)
