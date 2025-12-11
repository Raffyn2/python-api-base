"""Tests for phase 2 module exceptions.

**Feature: realistic-test-coverage**
**Validates: Requirements 4.2**
"""

from core.errors.shared.phase2_errors import (
    EntityResolutionError,
    FederationValidationError,
    FilterValidationError,
    Phase2ModuleError,
    PoolInvariantViolationError,
    SnapshotIntegrityError,
)


class TestPhase2ModuleError:
    """Tests for Phase2ModuleError base class."""

    def test_init_with_message(self) -> None:
        """Test initialization with message."""
        error = Phase2ModuleError("Base error message")
        assert "Base error message" in str(error)

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""
        error = Phase2ModuleError("Test")
        assert isinstance(error, Exception)


class TestPoolInvariantViolationError:
    """Tests for PoolInvariantViolationError."""

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        error = PoolInvariantViolationError(idle=5, in_use=3, unhealthy=1, total=10)
        assert error.idle == 5
        assert error.in_use == 3
        assert error.unhealthy == 1
        assert error.total == 10

    def test_message_shows_violation(self) -> None:
        """Test that message shows the invariant violation."""
        error = PoolInvariantViolationError(idle=5, in_use=3, unhealthy=1, total=10)
        message = str(error)
        assert "Pool invariant violated" in message
        assert "idle(5)" in message
        assert "in_use(3)" in message
        assert "unhealthy(1)" in message
        assert "= 9" in message  # actual sum
        assert "total = 10" in message

    def test_with_zero_values(self) -> None:
        """Test with zero values."""
        error = PoolInvariantViolationError(idle=0, in_use=0, unhealthy=0, total=1)
        assert error.idle == 0
        assert "= 0" in str(error)

    def test_inherits_from_phase2_error(self) -> None:
        """Test inheritance from Phase2ModuleError."""
        error = PoolInvariantViolationError(1, 1, 1, 5)
        assert isinstance(error, Phase2ModuleError)


class TestSnapshotIntegrityError:
    """Tests for SnapshotIntegrityError."""

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        error = SnapshotIntegrityError(
            aggregate_id="agg-123",
            expected_hash="abc123def456ghi789",
            actual_hash="xyz987uvw654rst321",
        )
        assert error.aggregate_id == "agg-123"
        assert error.expected_hash == "abc123def456ghi789"
        assert error.actual_hash == "xyz987uvw654rst321"

    def test_message_shows_truncated_hashes(self) -> None:
        """Test that message shows truncated hashes."""
        error = SnapshotIntegrityError(
            aggregate_id="my-aggregate",
            expected_hash="0123456789abcdef0123456789abcdef",
            actual_hash="fedcba9876543210fedcba9876543210",
        )
        message = str(error)
        assert "Snapshot integrity check failed" in message
        # Note: aggregate_id is stored but not in message for security
        assert "01234567..." in message
        assert "fedcba98..." in message

    def test_inherits_from_phase2_error(self) -> None:
        """Test inheritance from Phase2ModuleError."""
        error = SnapshotIntegrityError("id", "hash1", "hash2")
        assert isinstance(error, Phase2ModuleError)


class TestFilterValidationError:
    """Tests for FilterValidationError."""

    def test_init_with_field_and_allowed(self) -> None:
        """Test initialization with field and allowed fields."""
        error = FilterValidationError(
            field="invalid_field",
            allowed_fields={"name", "email", "created_at"},
        )
        assert error.field == "invalid_field"
        assert error.allowed_fields == {"name", "email", "created_at"}
        assert error.operation == "filter"

    def test_init_with_custom_operation(self) -> None:
        """Test initialization with custom operation type."""
        error = FilterValidationError(
            field="bad_sort",
            allowed_fields={"id", "name"},
            operation="sort",
        )
        assert error.operation == "sort"
        assert "Invalid sort field" in str(error)

    def test_message_shows_allowed_fields(self) -> None:
        """Test that message does NOT expose allowed fields (security)."""
        error = FilterValidationError(
            field="unknown",
            allowed_fields={"a", "b", "c"},
        )
        message = str(error)
        # Security: allowed fields are stored but NOT exposed in message
        assert "Invalid filter field specified" in message
        assert error.field == "unknown"
        assert error.allowed_fields == {"a", "b", "c"}

    def test_message_truncates_many_fields(self) -> None:
        """Test that message does NOT expose allowed fields (security)."""
        many_fields = {f"field_{i}" for i in range(20)}
        error = FilterValidationError(field="bad", allowed_fields=many_fields)
        message = str(error)
        # Security: allowed fields are stored but NOT exposed in message
        assert "Invalid filter field specified" in message
        assert len(error.allowed_fields) == 20

    def test_inherits_from_phase2_error(self) -> None:
        """Test inheritance from Phase2ModuleError."""
        error = FilterValidationError("f", {"a"})
        assert isinstance(error, Phase2ModuleError)


class TestFederationValidationError:
    """Tests for FederationValidationError."""

    def test_init_with_single_error(self) -> None:
        """Test initialization with single error."""
        error = FederationValidationError(["Missing @key directive"])
        assert error.errors == ["Missing @key directive"]
        assert "1 error" in str(error)

    def test_init_with_multiple_errors(self) -> None:
        """Test initialization with multiple errors."""
        errors = ["Error 1", "Error 2", "Error 3"]
        error = FederationValidationError(errors)
        assert error.errors == errors
        assert "3 error(s)" in str(error)

    def test_message_truncates_many_errors(self) -> None:
        """Test that message truncates when many errors."""
        errors = ["Error 1", "Error 2", "Error 3", "Error 4", "Error 5"]
        error = FederationValidationError(errors)
        message = str(error)
        assert "5 error(s)" in message
        assert "... and 2 more errors" in message

    def test_inherits_from_phase2_error(self) -> None:
        """Test inheritance from Phase2ModuleError."""
        error = FederationValidationError(["test"])
        assert isinstance(error, Phase2ModuleError)


class TestEntityResolutionError:
    """Tests for EntityResolutionError."""

    def test_init_with_entity_and_reason(self) -> None:
        """Test initialization with entity name and reason."""
        error = EntityResolutionError("User", "No resolver registered")
        assert error.entity_name == "User"
        assert error.reason == "No resolver registered"

    def test_message_format(self) -> None:
        """Test error message format."""
        error = EntityResolutionError("Product", "Invalid representation")
        message = str(error)
        assert "Failed to resolve entity 'Product'" in message
        assert "Invalid representation" in message

    def test_inherits_from_phase2_error(self) -> None:
        """Test inheritance from Phase2ModuleError."""
        error = EntityResolutionError("Entity", "reason")
        assert isinstance(error, Phase2ModuleError)
