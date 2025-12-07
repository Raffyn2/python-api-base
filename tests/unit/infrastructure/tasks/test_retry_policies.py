"""Unit tests for task retry policies.

Tests NoRetry, FixedDelay, and ExponentialBackoff policies.
"""

import pytest

from infrastructure.tasks.retry import (
    DEFAULT_RETRY_POLICY,
    ExponentialBackoff,
    FixedDelay,
    NoRetry,
    RetryPolicy,
)


class TestNoRetry:
    """Tests for NoRetry policy."""

    def test_get_delay_returns_zero(self) -> None:
        """Test get_delay always returns 0."""
        policy = NoRetry()

        assert policy.get_delay(1) == 0.0
        assert policy.get_delay(5) == 0.0

    def test_should_retry_always_false(self) -> None:
        """Test should_retry always returns False."""
        policy = NoRetry()

        assert policy.should_retry(1, 3) is False
        assert policy.should_retry(1, 10) is False

    def test_is_retry_policy(self) -> None:
        """Test NoRetry is a RetryPolicy."""
        policy = NoRetry()

        assert isinstance(policy, RetryPolicy)


class TestFixedDelay:
    """Tests for FixedDelay policy."""

    def test_default_delay(self) -> None:
        """Test default delay value."""
        policy = FixedDelay()

        assert policy.delay_seconds == 5.0

    def test_custom_delay(self) -> None:
        """Test custom delay value."""
        policy = FixedDelay(delay_seconds=10.0)

        assert policy.delay_seconds == 10.0

    def test_get_delay_returns_fixed(self) -> None:
        """Test get_delay returns fixed delay."""
        policy = FixedDelay(delay_seconds=3.0)

        assert policy.get_delay(1) == 3.0
        assert policy.get_delay(5) == 3.0
        assert policy.get_delay(10) == 3.0

    def test_should_retry_under_max(self) -> None:
        """Test should_retry returns True under max attempts."""
        policy = FixedDelay()

        assert policy.should_retry(1, 3) is True
        assert policy.should_retry(2, 3) is True

    def test_should_retry_at_max(self) -> None:
        """Test should_retry returns False at max attempts."""
        policy = FixedDelay()

        assert policy.should_retry(3, 3) is False
        assert policy.should_retry(4, 3) is False

    def test_is_retry_policy(self) -> None:
        """Test FixedDelay is a RetryPolicy."""
        policy = FixedDelay()

        assert isinstance(policy, RetryPolicy)


class TestExponentialBackoff:
    """Tests for ExponentialBackoff policy."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        policy = ExponentialBackoff()

        assert policy.base_delay == 1.0
        assert policy.multiplier == 2.0
        assert policy.max_delay == 300.0
        assert policy.jitter == 0.1

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        policy = ExponentialBackoff(
            base_delay=2.0,
            multiplier=3.0,
            max_delay=60.0,
            jitter=0.0,
        )

        assert policy.base_delay == 2.0
        assert policy.multiplier == 3.0
        assert policy.max_delay == 60.0
        assert policy.jitter == 0.0

    def test_get_delay_exponential_no_jitter(self) -> None:
        """Test exponential delay calculation without jitter."""
        policy = ExponentialBackoff(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=100.0,
            jitter=0.0,
        )

        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 4.0
        assert policy.get_delay(4) == 8.0

    def test_get_delay_respects_max(self) -> None:
        """Test delay is capped at max_delay."""
        policy = ExponentialBackoff(
            base_delay=10.0,
            multiplier=2.0,
            max_delay=15.0,
            jitter=0.0,
        )

        assert policy.get_delay(1) == 10.0
        assert policy.get_delay(2) == 15.0  # Would be 20 without cap
        assert policy.get_delay(3) == 15.0  # Would be 40 without cap

    def test_get_delay_with_jitter_varies(self) -> None:
        """Test delay with jitter varies."""
        policy = ExponentialBackoff(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=100.0,
            jitter=0.5,
        )

        delays = [policy.get_delay(1) for _ in range(10)]

        # With jitter, delays should vary
        assert len(set(delays)) > 1
        # All delays should be >= base_delay
        assert all(d >= 1.0 for d in delays)

    def test_should_retry_under_max(self) -> None:
        """Test should_retry returns True under max attempts."""
        policy = ExponentialBackoff()

        assert policy.should_retry(1, 3) is True
        assert policy.should_retry(2, 3) is True

    def test_should_retry_at_max(self) -> None:
        """Test should_retry returns False at max attempts."""
        policy = ExponentialBackoff()

        assert policy.should_retry(3, 3) is False
        assert policy.should_retry(4, 3) is False

    def test_is_retry_policy(self) -> None:
        """Test ExponentialBackoff is a RetryPolicy."""
        policy = ExponentialBackoff()

        assert isinstance(policy, RetryPolicy)


class TestDefaultRetryPolicy:
    """Tests for default retry policy."""

    def test_default_is_exponential_backoff(self) -> None:
        """Test default policy is ExponentialBackoff."""
        assert isinstance(DEFAULT_RETRY_POLICY, ExponentialBackoff)

    def test_default_values(self) -> None:
        """Test default policy has expected values."""
        assert DEFAULT_RETRY_POLICY.base_delay == 1.0
        assert DEFAULT_RETRY_POLICY.multiplier == 2.0
