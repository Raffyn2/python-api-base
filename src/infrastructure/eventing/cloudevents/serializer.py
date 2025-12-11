"""CloudEvent serializer for structured and binary content modes."""

import base64
import json
from typing import Any

from infrastructure.eventing.cloudevents.models import (
    CloudEvent,
    CloudEventSerializationError,
)


class CloudEventSerializer:
    """Serializer for CloudEvents in structured and binary content modes."""

    @staticmethod
    def to_structured(event: CloudEvent) -> tuple[dict[str, str], bytes]:
        """Serialize CloudEvent to structured content mode (JSON body).

        Args:
            event: CloudEvent to serialize

        Returns:
            Tuple of (headers, body)
        """
        headers = {
            "Content-Type": "application/cloudevents+json; charset=utf-8",
        }

        body = json.dumps(event.to_dict(), default=str).encode("utf-8")
        return headers, body

    @staticmethod
    def to_binary(event: CloudEvent) -> tuple[dict[str, str], bytes]:
        """Serialize CloudEvent to binary content mode (headers + body).

        Args:
            event: CloudEvent to serialize

        Returns:
            Tuple of (headers, body)
        """
        headers: dict[str, str] = {
            "ce-specversion": event.specversion,
            "ce-id": event.id,
            "ce-source": event.source,
            "ce-type": event.type,
        }

        # Optional attributes
        if event.datacontenttype:
            headers["ce-datacontenttype"] = event.datacontenttype
            headers["Content-Type"] = event.datacontenttype
        else:
            headers["Content-Type"] = "application/json"

        if event.dataschema:
            headers["ce-dataschema"] = event.dataschema
        if event.subject:
            headers["ce-subject"] = event.subject
        if event.time:
            headers["ce-time"] = event.time.isoformat() + "Z"

        # Extension attributes
        for key, value in event.extensions.items():
            headers[f"ce-{key}"] = str(value)

        # Body
        if event.data_base64:
            body = base64.b64decode(event.data_base64)
        elif event.data is not None:
            body = json.dumps(event.data, default=str).encode("utf-8")
        else:
            body = b""

        return headers, body

    @staticmethod
    def serialize(event: CloudEvent, mode: str = "structured") -> tuple[dict[str, str], bytes]:
        """Serialize CloudEvent to specified content mode.

        Args:
            event: CloudEvent to serialize
            mode: Content mode ("structured" or "binary")

        Returns:
            Tuple of (headers, body)

        Raises:
            CloudEventSerializationError: If mode is invalid
        """
        if mode == "structured":
            return CloudEventSerializer.to_structured(event)
        if mode == "binary":
            return CloudEventSerializer.to_binary(event)
        raise CloudEventSerializationError(f"Invalid content mode: {mode}")

    @staticmethod
    def to_json(event: CloudEvent) -> str:
        """Serialize CloudEvent to JSON string.

        Args:
            event: CloudEvent to serialize

        Returns:
            JSON string representation
        """
        return json.dumps(event.to_dict(), default=str)

    @staticmethod
    def to_dict(event: CloudEvent) -> dict[str, Any]:
        """Serialize CloudEvent to dictionary.

        Args:
            event: CloudEvent to serialize

        Returns:
            Dictionary representation
        """
        return event.to_dict()
