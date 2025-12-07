"""Unit tests for status enums.

Tests BaseStatus, ConnectionStatus, TaskStatus, and related enums.
"""

from infrastructure.generics.core.status import (
    AuthStatus,
    BaseStatus,
    CacheStatus,
    ConnectionStatus,
    HealthStatus,
    MessageStatus,
    TaskStatus,
)


class TestBaseStatus:
    """Tests for BaseStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING value."""
        assert BaseStatus.PENDING.value == "pending"

    def test_active_value(self) -> None:
        """Test ACTIVE value."""
        assert BaseStatus.ACTIVE.value == "active"

    def test_completed_value(self) -> None:
        """Test COMPLETED value."""
        assert BaseStatus.COMPLETED.value == "completed"

    def test_failed_value(self) -> None:
        """Test FAILED value."""
        assert BaseStatus.FAILED.value == "failed"

    def test_cancelled_value(self) -> None:
        """Test CANCELLED value."""
        assert BaseStatus.CANCELLED.value == "cancelled"

    def test_is_str(self) -> None:
        """Test enum values are strings."""
        assert isinstance(BaseStatus.PENDING.value, str)
        assert isinstance(BaseStatus.PENDING, str)


class TestConnectionStatus:
    """Tests for ConnectionStatus enum."""

    def test_idle_value(self) -> None:
        """Test IDLE value."""
        assert ConnectionStatus.IDLE.value == "idle"

    def test_in_use_value(self) -> None:
        """Test IN_USE value."""
        assert ConnectionStatus.IN_USE.value == "in_use"

    def test_unhealthy_value(self) -> None:
        """Test UNHEALTHY value."""
        assert ConnectionStatus.UNHEALTHY.value == "unhealthy"

    def test_closed_value(self) -> None:
        """Test CLOSED value."""
        assert ConnectionStatus.CLOSED.value == "closed"


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING value."""
        assert TaskStatus.PENDING.value == "pending"

    def test_running_value(self) -> None:
        """Test RUNNING value."""
        assert TaskStatus.RUNNING.value == "running"

    def test_completed_value(self) -> None:
        """Test COMPLETED value."""
        assert TaskStatus.COMPLETED.value == "completed"

    def test_failed_value(self) -> None:
        """Test FAILED value."""
        assert TaskStatus.FAILED.value == "failed"

    def test_retrying_value(self) -> None:
        """Test RETRYING value."""
        assert TaskStatus.RETRYING.value == "retrying"


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_healthy_value(self) -> None:
        """Test HEALTHY value."""
        assert HealthStatus.HEALTHY.value == "healthy"

    def test_degraded_value(self) -> None:
        """Test DEGRADED value."""
        assert HealthStatus.DEGRADED.value == "degraded"

    def test_unhealthy_value(self) -> None:
        """Test UNHEALTHY value."""
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestCacheStatus:
    """Tests for CacheStatus enum."""

    def test_valid_value(self) -> None:
        """Test VALID value."""
        assert CacheStatus.VALID.value == "valid"

    def test_expired_value(self) -> None:
        """Test EXPIRED value."""
        assert CacheStatus.EXPIRED.value == "expired"

    def test_invalidated_value(self) -> None:
        """Test INVALIDATED value."""
        assert CacheStatus.INVALIDATED.value == "invalidated"


class TestMessageStatus:
    """Tests for MessageStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING value."""
        assert MessageStatus.PENDING.value == "pending"

    def test_processing_value(self) -> None:
        """Test PROCESSING value."""
        assert MessageStatus.PROCESSING.value == "processing"

    def test_delivered_value(self) -> None:
        """Test DELIVERED value."""
        assert MessageStatus.DELIVERED.value == "delivered"

    def test_dead_letter_value(self) -> None:
        """Test DEAD_LETTER value."""
        assert MessageStatus.DEAD_LETTER.value == "dead_letter"


class TestAuthStatus:
    """Tests for AuthStatus enum."""

    def test_valid_value(self) -> None:
        """Test VALID value."""
        assert AuthStatus.VALID.value == "valid"

    def test_expired_value(self) -> None:
        """Test EXPIRED value."""
        assert AuthStatus.EXPIRED.value == "expired"

    def test_revoked_value(self) -> None:
        """Test REVOKED value."""
        assert AuthStatus.REVOKED.value == "revoked"

    def test_invalid_value(self) -> None:
        """Test INVALID value."""
        assert AuthStatus.INVALID.value == "invalid"
