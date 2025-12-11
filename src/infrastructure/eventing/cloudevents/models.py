"""CloudEvents v1.0 specification models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Self
from uuid import uuid4


@dataclass(slots=True)
class CloudEvent:
    """CloudEvents v1.0 specification model.

    Implements the CloudEvents specification v1.0 for event-driven architectures.
    https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
    """

    # Required attributes
    id: str
    source: str
    type: str
    specversion: str = "1.0"

    # Optional attributes
    datacontenttype: str | None = "application/json"
    dataschema: str | None = None
    subject: str | None = None
    time: datetime | None = None

    # Event data
    data: dict[str, Any] | None = None
    data_base64: str | None = None

    # Extension attributes
    extensions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate required attributes after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate CloudEvent required attributes.

        Raises:
            CloudEventValidationError: If required attributes are missing or invalid.
        """
        if not self.id:
            raise CloudEventValidationError("CloudEvent 'id' is required")
        if not self.source:
            raise CloudEventValidationError("CloudEvent 'source' is required")
        if not self.type:
            raise CloudEventValidationError("CloudEvent 'type' is required")
        if self.specversion != "1.0":
            raise CloudEventValidationError(f"Unsupported specversion: {self.specversion}. Only '1.0' is supported")

    @classmethod
    def create(
        cls,
        source: str,
        event_type: str,
        data: dict[str, Any] | None = None,
        subject: str | None = None,
        datacontenttype: str = "application/json",
        extensions: dict[str, Any] | None = None,
    ) -> Self:
        """Factory method to create a new CloudEvent with auto-generated id and time.

        Args:
            source: Event source URI
            event_type: Event type identifier
            data: Event payload
            subject: Event subject
            datacontenttype: Content type of data
            extensions: Extension attributes

        Returns:
            New CloudEvent instance
        """
        return cls(
            id=str(uuid4()),
            source=source,
            type=event_type,
            time=datetime.now(UTC),
            data=data,
            subject=subject,
            datacontenttype=datacontenttype,
            extensions=extensions or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert CloudEvent to dictionary representation.

        Returns:
            Dictionary with all CloudEvent attributes
        """
        result: dict[str, Any] = {
            "specversion": self.specversion,
            "id": self.id,
            "source": self.source,
            "type": self.type,
        }

        if self.datacontenttype:
            result["datacontenttype"] = self.datacontenttype
        if self.dataschema:
            result["dataschema"] = self.dataschema
        if self.subject:
            result["subject"] = self.subject
        if self.time:
            # Format as ISO 8601 with Z suffix for UTC
            time_str = self.time.isoformat()
            if time_str.endswith("+00:00"):
                time_str = time_str[:-6] + "Z"
            elif not time_str.endswith("Z"):
                time_str = time_str + "Z"
            result["time"] = time_str
        if self.data is not None:
            result["data"] = self.data
        if self.data_base64:
            result["data_base64"] = self.data_base64

        # Add extension attributes
        result.update(self.extensions)

        return result

    def __eq__(self, other: object) -> bool:
        """Check equality with another CloudEvent."""
        if not isinstance(other, CloudEvent):
            return False
        return (
            self.id == other.id
            and self.source == other.source
            and self.type == other.type
            and self.specversion == other.specversion
            and self.datacontenttype == other.datacontenttype
            and self.dataschema == other.dataschema
            and self.subject == other.subject
            and self.data == other.data
            and self.data_base64 == other.data_base64
            and self.extensions == other.extensions
        )


class CloudEventError(Exception):
    """Base error for CloudEvent issues."""


class CloudEventValidationError(CloudEventError):
    """CloudEvent missing required attributes or invalid values."""


class CloudEventSerializationError(CloudEventError):
    """Error serializing/deserializing CloudEvent."""
