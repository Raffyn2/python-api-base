"""Protobuf mapper utilities.

This module provides base classes and utilities for mapping
between domain entities and Protocol Buffer messages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from datetime import datetime

    from google.protobuf.timestamp_pb2 import Timestamp

TEntity = TypeVar("TEntity")
TProto = TypeVar("TProto")


class ProtobufMapper[TEntity, TProto](ABC):
    """Abstract base class for entity <-> protobuf mapping.

    This class defines the interface for bidirectional mapping
    between domain entities and Protocol Buffer messages.
    """

    @abstractmethod
    def to_proto(self, entity: TEntity) -> TProto:
        """Convert domain entity to protobuf message.

        Args:
            entity: The domain entity

        Returns:
            The protobuf message
        """
        ...

    @abstractmethod
    def from_proto(self, proto: TProto) -> TEntity:
        """Convert protobuf message to domain entity.

        Args:
            proto: The protobuf message

        Returns:
            The domain entity
        """
        ...

    def to_proto_list(self, entities: list[TEntity]) -> list[TProto]:
        """Convert list of entities to list of protobuf messages.

        Args:
            entities: List of domain entities

        Returns:
            List of protobuf messages
        """
        return [self.to_proto(entity) for entity in entities]

    def from_proto_list(self, protos: list[TProto]) -> list[TEntity]:
        """Convert list of protobuf messages to list of entities.

        Args:
            protos: List of protobuf messages

        Returns:
            List of domain entities
        """
        return [self.from_proto(proto) for proto in protos]


class TimestampMapper:
    """Utility class for timestamp conversions."""

    @staticmethod
    def to_proto_timestamp(dt: datetime | None) -> Timestamp | None:
        """Convert datetime to protobuf Timestamp.

        Args:
            dt: Python datetime object

        Returns:
            Protobuf Timestamp message
        """
        if dt is None:
            return None

        from google.protobuf.timestamp_pb2 import Timestamp

        ts = Timestamp()
        ts.FromDatetime(dt)
        return ts

    @staticmethod
    def from_proto_timestamp(ts: Timestamp | None) -> datetime | None:
        """Convert protobuf Timestamp to datetime.

        Args:
            ts: Protobuf Timestamp message

        Returns:
            Python datetime object
        """
        if ts is None:
            return None

        if hasattr(ts, "ToDatetime"):
            return ts.ToDatetime()
        return None


class OptionalFieldMapper:
    """Utility class for handling optional protobuf fields."""

    @staticmethod
    def get_optional(proto: object, field_name: str, default: object = None) -> object:
        """Get optional field value from protobuf message.

        Args:
            proto: The protobuf message
            field_name: Name of the field
            default: Default value if field is not set

        Returns:
            Field value or default
        """
        if hasattr(proto, "HasField"):
            try:
                if proto.HasField(field_name):
                    return getattr(proto, field_name)
            except ValueError:
                # Field is not a singular field
                pass

        value = getattr(proto, field_name, default)
        if value == "" or value == 0:
            return default
        return value

    @staticmethod
    def set_optional(proto: object, field_name: str, value: object) -> None:
        """Set optional field value on protobuf message.

        Args:
            proto: The protobuf message
            field_name: Name of the field
            value: Value to set (None to skip)
        """
        if value is not None:
            setattr(proto, field_name, value)
