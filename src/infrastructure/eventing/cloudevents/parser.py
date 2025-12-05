"""CloudEvent parser for structured and binary content modes."""

import json
from datetime import datetime
from typing import Any

from src.infrastructure.eventing.cloudevents.models import (
    CloudEvent,
    CloudEventSerializationError,
)


# CloudEvents HTTP header prefix for binary mode
CE_HEADER_PREFIX = "ce-"

# Required CloudEvents headers in binary mode
CE_REQUIRED_HEADERS = {
    "ce-id": "id",
    "ce-source": "source",
    "ce-type": "type",
    "ce-specversion": "specversion",
}

# Optional CloudEvents headers in binary mode
CE_OPTIONAL_HEADERS = {
    "ce-datacontenttype": "datacontenttype",
    "ce-dataschema": "dataschema",
    "ce-subject": "subject",
    "ce-time": "time",
}


class CloudEventParser:
    """Parser for CloudEvents in structured and binary content modes."""

    @staticmethod
    def parse_structured(body: bytes | str, content_type: str = "application/cloudevents+json") -> CloudEvent:
        """Parse CloudEvent from structured content mode (JSON body).

        Args:
            body: JSON body containing the CloudEvent
            content_type: Content-Type header value

        Returns:
            Parsed CloudEvent instance

        Raises:
            CloudEventSerializationError: If parsing fails
        """
        if not content_type.startswith("application/cloudevents"):
            raise CloudEventSerializationError(
                f"Invalid content type for structured mode: {content_type}"
            )

        try:
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise CloudEventSerializationError(f"Failed to parse JSON body: {e}") from e

        return CloudEventParser._dict_to_cloudevent(data)

    @staticmethod
    def parse_binary(headers: dict[str, str], body: bytes | str) -> CloudEvent:
        """Parse CloudEvent from binary content mode (headers + body).

        Args:
            headers: HTTP headers containing CloudEvent attributes
            body: Request body containing event data

        Returns:
            Parsed CloudEvent instance

        Raises:
            CloudEventSerializationError: If parsing fails
        """
        # Normalize headers to lowercase
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        # Extract required attributes
        attrs: dict[str, Any] = {}
        for header, attr in CE_REQUIRED_HEADERS.items():
            if header not in normalized_headers:
                raise CloudEventSerializationError(
                    f"Missing required CloudEvent header: {header}"
                )
            attrs[attr] = normalized_headers[header]

        # Extract optional attributes
        for header, attr in CE_OPTIONAL_HEADERS.items():
            if header in normalized_headers:
                value = normalized_headers[header]
                if attr == "time":
                    value = CloudEventParser._parse_time(value)
                attrs[attr] = value

        # Extract extension attributes
        extensions: dict[str, Any] = {}
        for key, value in normalized_headers.items():
            if key.startswith(CE_HEADER_PREFIX) and key not in CE_REQUIRED_HEADERS and key not in CE_OPTIONAL_HEADERS:
                ext_name = key[len(CE_HEADER_PREFIX):]
                extensions[ext_name] = value

        # Parse body as data
        content_type = normalized_headers.get("content-type", "application/json")
        if body:
            try:
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                if content_type.startswith("application/json"):
                    attrs["data"] = json.loads(body)
                else:
                    attrs["data"] = {"raw": body}
            except (json.JSONDecodeError, UnicodeDecodeError):
                attrs["data"] = {"raw": body if isinstance(body, str) else body.decode("utf-8", errors="replace")}

        attrs["extensions"] = extensions
        return CloudEvent(**attrs)

    @staticmethod
    def detect_content_mode(headers: dict[str, str]) -> str:
        """Detect CloudEvent content mode from headers.

        Args:
            headers: HTTP headers

        Returns:
            "structured" or "binary"
        """
        content_type = headers.get("content-type", headers.get("Content-Type", ""))
        if "application/cloudevents" in content_type:
            return "structured"
        return "binary"

    @staticmethod
    def parse(headers: dict[str, str], body: bytes | str) -> CloudEvent:
        """Parse CloudEvent auto-detecting content mode.

        Args:
            headers: HTTP headers
            body: Request body

        Returns:
            Parsed CloudEvent instance
        """
        mode = CloudEventParser.detect_content_mode(headers)
        if mode == "structured":
            content_type = headers.get("content-type", headers.get("Content-Type", "application/cloudevents+json"))
            return CloudEventParser.parse_structured(body, content_type)
        return CloudEventParser.parse_binary(headers, body)

    @staticmethod
    def _dict_to_cloudevent(data: dict[str, Any]) -> CloudEvent:
        """Convert dictionary to CloudEvent.

        Args:
            data: Dictionary with CloudEvent attributes

        Returns:
            CloudEvent instance
        """
        # Extract known attributes
        attrs: dict[str, Any] = {
            "id": data.get("id"),
            "source": data.get("source"),
            "type": data.get("type"),
            "specversion": data.get("specversion", "1.0"),
        }

        # Optional attributes
        if "datacontenttype" in data:
            attrs["datacontenttype"] = data["datacontenttype"]
        if "dataschema" in data:
            attrs["dataschema"] = data["dataschema"]
        if "subject" in data:
            attrs["subject"] = data["subject"]
        if "time" in data:
            attrs["time"] = CloudEventParser._parse_time(data["time"])
        if "data" in data:
            attrs["data"] = data["data"]
        if "data_base64" in data:
            attrs["data_base64"] = data["data_base64"]

        # Extension attributes (anything not in known attributes)
        known_attrs = {
            "specversion", "id", "source", "type", "datacontenttype",
            "dataschema", "subject", "time", "data", "data_base64"
        }
        extensions = {k: v for k, v in data.items() if k not in known_attrs}
        attrs["extensions"] = extensions

        return CloudEvent(**attrs)

    @staticmethod
    def _parse_time(value: str | datetime) -> datetime:
        """Parse time value to datetime.

        Args:
            value: ISO 8601 time string or datetime

        Returns:
            datetime instance
        """
        if isinstance(value, datetime):
            return value
        # Handle ISO 8601 format with Z suffix
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
