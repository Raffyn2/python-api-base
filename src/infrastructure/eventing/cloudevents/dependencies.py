"""FastAPI dependencies for CloudEvent handling."""

from typing import Annotated

from fastapi import Depends, Header, Request

from infrastructure.eventing.cloudevents.models import (
    CloudEvent,
    CloudEventSerializationError,
)
from infrastructure.eventing.cloudevents.parser import CloudEventParser


async def get_cloud_event(
    request: Request,
    content_type: Annotated[str | None, Header()] = None,
    ce_id: Annotated[str | None, Header(alias="ce-id")] = None,
    ce_source: Annotated[str | None, Header(alias="ce-source")] = None,
    ce_type: Annotated[str | None, Header(alias="ce-type")] = None,
    ce_specversion: Annotated[str | None, Header(alias="ce-specversion")] = None,
) -> CloudEvent:
    """FastAPI dependency to parse CloudEvent from request.

    Automatically detects content mode (structured or binary) and parses
    the CloudEvent from the request.

    Args:
        request: FastAPI request object
        content_type: Content-Type header
        ce_id: CloudEvent ID header (binary mode)
        ce_source: CloudEvent source header (binary mode)
        ce_type: CloudEvent type header (binary mode)
        ce_specversion: CloudEvent specversion header (binary mode)

    Returns:
        Parsed CloudEvent instance

    Raises:
        CloudEventSerializationError: If parsing fails
    """
    body = await request.body()
    headers = dict(request.headers)

    try:
        return CloudEventParser.parse(headers, body)
    except Exception as e:
        msg = "Failed to parse CloudEvent"
        raise CloudEventSerializationError(msg) from e


class CloudEventDependency:
    """Configurable CloudEvent dependency for FastAPI."""

    def __init__(self, required: bool = True, validate: bool = True) -> None:
        """Initialize CloudEvent dependency.

        Args:
            required: Whether CloudEvent is required
            validate: Whether to validate CloudEvent attributes
        """
        self.required = required
        self.validate = validate

    async def __call__(self, request: Request) -> CloudEvent | None:
        """Parse CloudEvent from request.

        Args:
            request: FastAPI request object

        Returns:
            Parsed CloudEvent or None if not required and missing
        """
        body = await request.body()
        headers = dict(request.headers)

        # Check if this looks like a CloudEvent
        content_type = headers.get("content-type", "")
        has_ce_headers = any(k.lower().startswith("ce-") for k in headers)

        is_cloudevent = content_type.startswith("application/cloudevents")
        if not is_cloudevent and not has_ce_headers:
            if self.required:
                raise CloudEventSerializationError("Request is not a CloudEvent")
            return None

        try:
            event = CloudEventParser.parse(headers, body)
            if self.validate:
                event.validate()
            return event
        except Exception as e:
            if self.required:
                msg = "Failed to parse CloudEvent"
                raise CloudEventSerializationError(msg) from e
            return None


# Pre-configured dependencies
RequiredCloudEvent = Annotated[CloudEvent, Depends(get_cloud_event)]
OptionalCloudEvent = Annotated[CloudEvent | None, Depends(CloudEventDependency(required=False))]
