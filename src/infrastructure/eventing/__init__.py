"""Eventing infrastructure for CloudEvents and Knative integration."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.eventing.cloudevents.dependencies import get_cloud_event
    from infrastructure.eventing.cloudevents.models import CloudEvent
    from infrastructure.eventing.cloudevents.parser import CloudEventParser
    from infrastructure.eventing.cloudevents.serializer import CloudEventSerializer

__all__ = [
    "CloudEvent",
    "CloudEventParser",
    "CloudEventSerializer",
    "get_cloud_event",
]


def __getattr__(name: str):
    """Lazy import to avoid circular imports."""
    if name == "CloudEvent":
        from infrastructure.eventing.cloudevents.models import CloudEvent

        return CloudEvent
    if name == "CloudEventParser":
        from infrastructure.eventing.cloudevents.parser import CloudEventParser

        return CloudEventParser
    if name == "CloudEventSerializer":
        from infrastructure.eventing.cloudevents.serializer import CloudEventSerializer

        return CloudEventSerializer
    if name == "get_cloud_event":
        from infrastructure.eventing.cloudevents.dependencies import get_cloud_event

        return get_cloud_event
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
