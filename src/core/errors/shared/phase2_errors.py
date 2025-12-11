"""Phase 2 module exceptions.

**Feature: shared-modules-phase2**
**Validates: Requirements 2.3, 6.2, 13.1, 15.3**
**Refactored: Split from exceptions.py for one-class-per-file compliance**
"""

from __future__ import annotations

from core.errors.shared.base import SharedModuleError


class Phase2ModuleError(SharedModuleError):
    """Base exception for phase 2 module errors.

    All phase 2 custom exceptions should inherit from this class.
    """


class PoolInvariantViolationError(Phase2ModuleError):
    """Connection pool counter invariant violated.

    Raised when the pool's counter invariant (idle + in_use + unhealthy == total)
    is violated.

    Attributes:
        idle: Number of idle connections.
        in_use: Number of connections in use.
        unhealthy: Number of unhealthy connections.
        total: Total number of connections.
    """

    def __init__(
        self,
        idle: int,
        in_use: int,
        unhealthy: int,
        total: int,
    ) -> None:
        """Initialize pool invariant violation error.

        Args:
            idle: Number of idle connections.
            in_use: Number of connections in use.
            unhealthy: Number of unhealthy connections.
            total: Total number of connections.
        """
        self.idle = idle
        self.in_use = in_use
        self.unhealthy = unhealthy
        self.total = total
        actual_sum = idle + in_use + unhealthy
        super().__init__(
            f"Pool invariant violated: idle({idle}) + in_use({in_use}) + "
            f"unhealthy({unhealthy}) = {actual_sum}, expected total = {total}"
        )


class SnapshotIntegrityError(Phase2ModuleError):
    """Snapshot integrity check failed.

    Raised when a snapshot's state hash doesn't match the expected hash.

    Note:
        Hash values are truncated in the error message to prevent
        exposing full cryptographic details.

    Attributes:
        aggregate_id: ID of the aggregate with corrupted snapshot.
        expected_hash: Expected hash value (stored, truncated in message).
        actual_hash: Actual computed hash value (stored, truncated in message).
    """

    def __init__(
        self,
        aggregate_id: str,
        expected_hash: str,
        actual_hash: str,
    ) -> None:
        """Initialize snapshot integrity error.

        Args:
            aggregate_id: ID of the aggregate with corrupted snapshot.
            expected_hash: Expected hash value.
            actual_hash: Actual computed hash value.
        """
        self.aggregate_id = aggregate_id
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        # Security: Truncate hashes to prevent full exposure
        expected_prefix = expected_hash[:8] if len(expected_hash) >= 8 else expected_hash
        actual_prefix = actual_hash[:8] if len(actual_hash) >= 8 else actual_hash
        super().__init__(
            f"Snapshot integrity check failed for aggregate: "
            f"hash mismatch (expected: {expected_prefix}..., got: {actual_prefix}...)"
        )


class FilterValidationError(Phase2ModuleError):
    """Filter field validation failed.

    Raised when a filter or sort field is not in the allowed list.

    Note:
        Allowed fields are stored but NOT exposed in the error message
        to prevent information leakage about internal data structure.

    Attributes:
        field: The invalid field name.
        allowed_fields: Set of allowed field names (stored, not exposed).
        operation: The operation type ('filter' or 'sort').
    """

    def __init__(
        self,
        field: str,
        allowed_fields: set[str],
        operation: str = "filter",
    ) -> None:
        """Initialize filter validation error.

        Args:
            field: The invalid field name.
            allowed_fields: Set of allowed field names (stored, not exposed).
            operation: The operation type ('filter' or 'sort').
        """
        self.field = field
        self.allowed_fields = allowed_fields
        self.operation = operation
        # Security: Do not expose allowed fields to prevent info leak
        super().__init__(f"Invalid {operation} field specified")


class FederationValidationError(Phase2ModuleError):
    """Federation schema validation failed.

    Raised when GraphQL federation schema validation fails with one or more errors.

    Attributes:
        errors: List of validation error messages.
    """

    def __init__(self, errors: list[str]) -> None:
        """Initialize federation validation error.

        Args:
            errors: List of validation error messages.
        """
        self.errors = errors
        error_count = len(errors)
        error_summary = "; ".join(errors[:3])
        if error_count > 3:
            error_summary += f" ... and {error_count - 3} more errors"
        super().__init__(f"Federation schema validation failed with {error_count} error(s): {error_summary}")


class EntityResolutionError(Phase2ModuleError):
    """Entity resolution failed.

    Raised when entity resolution fails due to missing resolver or invalid representation.

    Attributes:
        entity_name: Name of the entity that failed resolution.
        reason: Reason for the failure.
    """

    def __init__(self, entity_name: str, reason: str) -> None:
        """Initialize entity resolution error.

        Args:
            entity_name: Name of the entity that failed resolution.
            reason: Reason for the failure.
        """
        self.entity_name = entity_name
        self.reason = reason
        super().__init__(f"Failed to resolve entity '{entity_name}': {reason}")
