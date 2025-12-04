"""Generic Kafka infrastructure.

Provides type-safe Kafka producer and consumer with PEP 695 generics.

**Feature: observability-infrastructure**
**Feature: kafka-workflow-integration**
**Requirement: R3 - Generic Kafka Producer/Consumer**
**Requirement: R3.1 - Transactional Producer with Exactly-Once Semantics**
"""

from infrastructure.kafka.config import KafkaConfig
from infrastructure.kafka.consumer import KafkaConsumer
from infrastructure.kafka.event_publisher import (
    DomainEvent,
    EventPublisher,
    ItemCreatedEvent,
    ItemDeletedEvent,
    ItemUpdatedEvent,
    KafkaEventPublisher,
    NoOpEventPublisher,
    create_event_publisher,
)
from infrastructure.kafka.message import KafkaMessage, MessageMetadata
from infrastructure.kafka.producer import (
    KafkaProducer,
    TransactionalKafkaProducer,
    TransactionContext,
    TransactionError,
    TransactionResult,
    TransactionState,
)

__all__ = [
    # Event Publisher
    "DomainEvent",
    "EventPublisher",
    "ItemCreatedEvent",
    "ItemDeletedEvent",
    "ItemUpdatedEvent",
    # Config
    "KafkaConfig",
    # Consumer
    "KafkaConsumer",
    "KafkaEventPublisher",
    # Message
    "KafkaMessage",
    # Producer
    "KafkaProducer",
    "MessageMetadata",
    "NoOpEventPublisher",
    "TransactionContext",
    "TransactionError",
    "TransactionResult",
    "TransactionState",
    "TransactionalKafkaProducer",
    "create_event_publisher",
]
