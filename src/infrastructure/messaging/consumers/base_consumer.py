"""Base consumer pattern for message processing.

**Feature: architecture-restructuring-2025**
**Validates: Requirements 6.6**
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

import structlog

logger = structlog.get_logger(__name__)

TMessage = TypeVar("TMessage")


@dataclass(slots=True)
class ConsumerConfig:
    """Consumer configuration."""

    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    batch_size: int = 10
    prefetch_count: int = 10


class BaseConsumer[TMessage](ABC):
    """Base class for message consumers."""

    def __init__(self, config: ConsumerConfig | None = None) -> None:
        self._config = config or ConsumerConfig()
        self._running = False

    @abstractmethod
    async def process_message(self, message: TMessage) -> bool:
        """Process a single message. Return True on success."""
        ...

    @abstractmethod
    async def fetch_messages(self, batch_size: int) -> list[TMessage]:
        """Fetch batch of messages from source."""
        ...

    @abstractmethod
    async def acknowledge(self, message: TMessage) -> None:
        """Acknowledge successful message processing."""
        ...

    @abstractmethod
    async def reject(self, message: TMessage, requeue: bool = False) -> None:
        """Reject message, optionally requeuing."""
        ...

    async def start(self) -> None:
        """Start consuming messages."""
        self._running = True
        logger.info(
            "Starting consumer",
            operation="CONSUMER_START",
            consumer=self.__class__.__name__,
        )

        while self._running:
            try:
                messages = await self.fetch_messages(self._config.batch_size)
                for message in messages:
                    await self._process_with_retry(message)
            except Exception:
                logger.exception(
                    "Consumer error",
                    operation="CONSUMER_ERROR",
                )
                await asyncio.sleep(self._config.retry_delay_seconds)

    def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False
        logger.info(
            "Stopping consumer",
            operation="CONSUMER_STOP",
            consumer=self.__class__.__name__,
        )

    async def _process_with_retry(self, message: TMessage) -> None:
        """Process message with retry logic."""
        retries = 0
        while retries <= self._config.max_retries:
            try:
                success = await self.process_message(message)
                if success:
                    await self.acknowledge(message)
                    return
                retries += 1
            except Exception:
                logger.warning(
                    "Processing failed",
                    operation="CONSUMER_PROCESS",
                    attempt=retries + 1,
                    exc_info=True,
                )
                retries += 1
                if retries <= self._config.max_retries:
                    await asyncio.sleep(self._config.retry_delay_seconds * retries)

        # Max retries exceeded - send to DLQ
        await self.reject(message, requeue=False)
        logger.error(
            "Message sent to DLQ after max retries",
            operation="CONSUMER_DLQ",
            max_retries=self._config.max_retries,
        )
