"""Tests for base consumer module.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 6.6 - Message Consumer Pattern**
"""

import pytest

from infrastructure.messaging.consumers.base_consumer import (
    BaseConsumer,
    ConsumerConfig,
)


class TestConsumerConfig:
    """Tests for ConsumerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConsumerConfig()
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1.0
        assert config.batch_size == 10
        assert config.prefetch_count == 10

    def test_custom_max_retries(self) -> None:
        """Test custom max_retries."""
        config = ConsumerConfig(max_retries=5)
        assert config.max_retries == 5

    def test_custom_retry_delay(self) -> None:
        """Test custom retry_delay_seconds."""
        config = ConsumerConfig(retry_delay_seconds=2.5)
        assert config.retry_delay_seconds == 2.5

    def test_custom_batch_size(self) -> None:
        """Test custom batch_size."""
        config = ConsumerConfig(batch_size=20)
        assert config.batch_size == 20

    def test_custom_prefetch_count(self) -> None:
        """Test custom prefetch_count."""
        config = ConsumerConfig(prefetch_count=5)
        assert config.prefetch_count == 5


class ConcreteConsumer(BaseConsumer[str]):
    """Concrete implementation for testing."""

    def __init__(self, config: ConsumerConfig | None = None) -> None:
        super().__init__(config)
        self.processed_messages: list[str] = []
        self.acknowledged_messages: list[str] = []
        self.rejected_messages: list[tuple[str, bool]] = []
        self.messages_to_return: list[str] = []
        self.process_should_fail = False
        self.process_fail_count = 0

    async def process_message(self, message: str) -> bool:
        if self.process_should_fail:
            self.process_fail_count += 1
            raise ValueError("Processing failed")
        self.processed_messages.append(message)
        return True

    async def fetch_messages(self, batch_size: int) -> list[str]:
        messages = self.messages_to_return[:batch_size]
        self.messages_to_return = self.messages_to_return[batch_size:]
        return messages

    async def acknowledge(self, message: str) -> None:
        self.acknowledged_messages.append(message)

    async def reject(self, message: str, requeue: bool = False) -> None:
        self.rejected_messages.append((message, requeue))


class TestBaseConsumerInit:
    """Tests for BaseConsumer initialization."""

    def test_default_config(self) -> None:
        """Test initialization with default config."""
        consumer = ConcreteConsumer()
        assert consumer._config.max_retries == 3
        assert consumer._running is False

    def test_custom_config(self) -> None:
        """Test initialization with custom config."""
        config = ConsumerConfig(max_retries=5)
        consumer = ConcreteConsumer(config)
        assert consumer._config.max_retries == 5


class TestBaseConsumerStop:
    """Tests for stop method."""

    def test_stop_sets_running_false(self) -> None:
        """Test that stop sets _running to False."""
        consumer = ConcreteConsumer()
        consumer._running = True
        consumer.stop()
        assert consumer._running is False


class TestBaseConsumerProcessWithRetry:
    """Tests for _process_with_retry method."""

    @pytest.mark.asyncio
    async def test_successful_processing(self) -> None:
        """Test successful message processing."""
        consumer = ConcreteConsumer()
        await consumer._process_with_retry("test_message")
        assert "test_message" in consumer.processed_messages
        assert "test_message" in consumer.acknowledged_messages

    @pytest.mark.asyncio
    async def test_processing_failure_retries(self) -> None:
        """Test that processing retries on failure."""
        config = ConsumerConfig(max_retries=2, retry_delay_seconds=0.01)
        consumer = ConcreteConsumer(config)
        consumer.process_should_fail = True

        await consumer._process_with_retry("test_message")

        # Should have tried max_retries + 1 times
        assert consumer.process_fail_count == 3
        # Message should be rejected after max retries
        assert ("test_message", False) in consumer.rejected_messages

    @pytest.mark.asyncio
    async def test_processing_returns_false(self) -> None:
        """Test handling when process_message returns False."""
        config = ConsumerConfig(max_retries=1, retry_delay_seconds=0.01)
        consumer = ConcreteConsumer(config)

        # Override to return False
        async def return_false(msg: str) -> bool:
            return False

        consumer.process_message = return_false  # type: ignore

        await consumer._process_with_retry("test_message")
        # Should be rejected after retries
        assert ("test_message", False) in consumer.rejected_messages


class TestBaseConsumerStart:
    """Tests for start method."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self) -> None:
        """Test that start sets _running to True initially."""
        consumer = ConcreteConsumer()
        consumer.messages_to_return = []

        # Stop immediately after first iteration

        async def fetch_and_stop(batch_size: int) -> list[str]:
            consumer.stop()
            return []

        consumer.fetch_messages = fetch_and_stop  # type: ignore

        await consumer.start()
        # After stop, _running should be False
        assert consumer._running is False

    @pytest.mark.asyncio
    async def test_start_processes_single_batch(self) -> None:
        """Test that start processes a single batch of messages."""
        consumer = ConcreteConsumer()

        call_count = 0

        async def fetch_once(batch_size: int) -> list[str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ["msg1"]
            consumer.stop()
            return []

        consumer.fetch_messages = fetch_once  # type: ignore

        await consumer.start()
        assert "msg1" in consumer.processed_messages
        assert "msg1" in consumer.acknowledged_messages
