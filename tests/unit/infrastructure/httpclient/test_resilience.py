"""Tests for HTTP client resilience patterns.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from datetime import timedelta
from unittest.mock import patch

import pytest

from infrastructure.httpclient.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    HttpClientConfig,
    RetryPolicy,
)


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_closed_value(self) -> None:
        """Test CLOSED state value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self) -> None:
        """Test OPEN state value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self) -> None:
        """Test HALF_OPEN state value."""
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestRetryPolicy:
    """Tests for RetryPolicy."""

    def test_default_values(self) -> None:
        """Test default retry policy values."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.base_delay == timedelta(seconds=1)
        assert policy.max_delay == timedelta(seconds=30)
        assert policy.exponential_base == 2.0
        assert 429 in policy.retry_on_status
        assert 500 in policy.retry_on_status

    def test_custom_max_retries(self) -> None:
        """Test custom max retries."""
        policy = RetryPolicy(max_retries=5)
        assert policy.max_retries == 5

    def test_custom_base_delay(self) -> None:
        """Test custom base delay."""
        policy = RetryPolicy(base_delay=timedelta(seconds=2))
        assert policy.base_delay == timedelta(seconds=2)

    def test_custom_max_delay(self) -> None:
        """Test custom max delay."""
        policy = RetryPolicy(max_delay=timedelta(seconds=60))
        assert policy.max_delay == timedelta(seconds=60)

    def test_custom_exponential_base(self) -> None:
        """Test custom exponential base."""
        policy = RetryPolicy(exponential_base=3.0)
        assert policy.exponential_base == 3.0

    def test_custom_retry_on_status(self) -> None:
        """Test custom retry on status codes."""
        policy = RetryPolicy(retry_on_status=frozenset({500, 502}))
        assert policy.retry_on_status == frozenset({500, 502})

    def test_get_delay_first_attempt(self) -> None:
        """Test delay for first attempt."""
        policy = RetryPolicy(base_delay=timedelta(seconds=1))
        delay = policy.get_delay(0)
        assert delay == timedelta(seconds=1)

    def test_get_delay_second_attempt(self) -> None:
        """Test delay for second attempt with exponential backoff."""
        policy = RetryPolicy(
            base_delay=timedelta(seconds=1),
            exponential_base=2.0,
        )
        delay = policy.get_delay(1)
        assert delay == timedelta(seconds=2)

    def test_get_delay_third_attempt(self) -> None:
        """Test delay for third attempt."""
        policy = RetryPolicy(
            base_delay=timedelta(seconds=1),
            exponential_base=2.0,
        )
        delay = policy.get_delay(2)
        assert delay == timedelta(seconds=4)

    def test_get_delay_respects_max_delay(self) -> None:
        """Test that delay respects max delay."""
        policy = RetryPolicy(
            base_delay=timedelta(seconds=10),
            max_delay=timedelta(seconds=30),
            exponential_base=2.0,
        )
        delay = policy.get_delay(5)  # Would be 320s without cap
        assert delay == timedelta(seconds=30)

    def test_frozen_dataclass(self) -> None:
        """Test that RetryPolicy is immutable."""
        policy = RetryPolicy()
        with pytest.raises(AttributeError):
            policy.max_retries = 10


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout == timedelta(seconds=30)

    def test_custom_failure_threshold(self) -> None:
        """Test custom failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=10)
        assert config.failure_threshold == 10

    def test_custom_success_threshold(self) -> None:
        """Test custom success threshold."""
        config = CircuitBreakerConfig(success_threshold=5)
        assert config.success_threshold == 5

    def test_custom_timeout(self) -> None:
        """Test custom timeout."""
        config = CircuitBreakerConfig(timeout=timedelta(seconds=60))
        assert config.timeout == timedelta(seconds=60)

    def test_frozen_dataclass(self) -> None:
        """Test that CircuitBreakerConfig is immutable."""
        config = CircuitBreakerConfig()
        with pytest.raises(AttributeError):
            config.failure_threshold = 10


class TestHttpClientConfig:
    """Tests for HttpClientConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = HttpClientConfig()
        assert config.base_url == ""
        assert config.timeout == timedelta(seconds=30)
        assert config.verify_ssl is True
        assert config.headers == {}

    def test_custom_base_url(self) -> None:
        """Test custom base URL."""
        config = HttpClientConfig(base_url="https://api.example.com")
        assert config.base_url == "https://api.example.com"

    def test_custom_timeout(self) -> None:
        """Test custom timeout."""
        config = HttpClientConfig(timeout=timedelta(seconds=60))
        assert config.timeout == timedelta(seconds=60)

    def test_custom_headers(self) -> None:
        """Test custom headers."""
        headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        config = HttpClientConfig(headers=headers)
        assert config.headers == headers

    def test_disable_ssl_verification(self) -> None:
        """Test disabling SSL verification."""
        config = HttpClientConfig(verify_ssl=False)
        assert config.verify_ssl is False

    def test_custom_retry_policy(self) -> None:
        """Test custom retry policy."""
        retry_policy = RetryPolicy(max_retries=5)
        config = HttpClientConfig(retry_policy=retry_policy)
        assert config.retry_policy.max_retries == 5

    def test_custom_circuit_breaker(self) -> None:
        """Test custom circuit breaker config."""
        cb_config = CircuitBreakerConfig(failure_threshold=10)
        config = HttpClientConfig(circuit_breaker=cb_config)
        assert config.circuit_breaker.failure_threshold == 10


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initial_state_is_closed(self) -> None:
        """Test that initial state is CLOSED."""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker(config)
        assert cb.state == CircuitState.CLOSED

    def test_is_closed_when_closed(self) -> None:
        """Test is_closed returns True when CLOSED."""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker(config)
        assert cb.is_closed is True

    def test_record_success_resets_failure_count(self) -> None:
        """Test that recording success resets failure count."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config)

        # Record some failures
        cb.record_failure()
        cb.record_failure()

        # Record success
        cb.record_success()

        # Should still be closed
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_failure_threshold(self) -> None:
        """Test circuit opens after reaching failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_is_closed_returns_false_when_open(self) -> None:
        """Test is_closed returns False when OPEN."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config)

        cb.record_failure()

        assert cb.is_closed is False

    def test_transitions_to_half_open_after_timeout(self) -> None:
        """Test circuit transitions to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=timedelta(seconds=1),
        )
        cb = CircuitBreaker(config)

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Mock time to simulate timeout
        with patch("time.time") as mock_time:
            mock_time.return_value = cb._last_failure_time + 2  # 2 seconds later
            assert cb.is_closed is True
            assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_threshold_in_half_open(self) -> None:
        """Test circuit closes after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=timedelta(seconds=1),
        )
        cb = CircuitBreaker(config)

        # Open the circuit
        cb.record_failure()

        # Transition to half-open
        with patch("time.time") as mock_time:
            mock_time.return_value = cb._last_failure_time + 2
            cb.is_closed  # Trigger state check

        # Record successes
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self) -> None:
        """Test failure in HALF_OPEN reopens circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=timedelta(seconds=1),
        )
        cb = CircuitBreaker(config)

        # Open the circuit
        cb.record_failure()

        # Transition to half-open
        with patch("time.time") as mock_time:
            mock_time.return_value = cb._last_failure_time + 2
            cb.is_closed

        assert cb.state == CircuitState.HALF_OPEN

        # Record failure
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
