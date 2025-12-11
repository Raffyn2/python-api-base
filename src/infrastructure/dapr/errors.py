"""Dapr-specific error classes.

This module provides custom exceptions for Dapr operations including
connection failures, timeouts, and general Dapr errors.
"""

from __future__ import annotations


class DaprError(Exception):
    """Base exception for all Dapr-related errors.

    All Dapr-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize DaprError.

        Args:
            message: Error message describing what went wrong.
            details: Optional dictionary with additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DaprConnectionError(DaprError):
    """Exception raised when connection to Dapr sidecar fails.

    This error occurs when the application cannot establish or maintain
    a connection to the Dapr sidecar.
    """

    def __init__(
        self,
        message: str = "Failed to connect to Dapr sidecar",
        details: dict | None = None,
    ) -> None:
        """Initialize DaprConnectionError.

        Args:
            message: Error message describing the connection failure.
            details: Optional dictionary with connection details.
        """
        super().__init__(message, details)


class DaprTimeoutError(DaprError):
    """Exception raised when a Dapr operation times out.

    This error occurs when a Dapr operation exceeds the configured
    timeout duration.
    """

    def __init__(
        self,
        message: str = "Dapr operation timed out",
        timeout_seconds: float | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize DaprTimeoutError.

        Args:
            message: Error message describing the timeout.
            timeout_seconds: The timeout duration that was exceeded.
            details: Optional dictionary with operation details.
        """
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds


class DaprInvocationError(DaprError):
    """Exception raised when a service invocation fails.

    This error occurs when invoking another service through Dapr fails.
    """

    def __init__(
        self,
        message: str = "Service invocation failed",
        app_id: str | None = None,
        method: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize DaprInvocationError.

        Args:
            message: Error message describing the invocation failure.
            app_id: The target application ID.
            method: The method that was being invoked.
            details: Optional dictionary with invocation details.
        """
        super().__init__(message, details)
        self.app_id = app_id
        self.method = method


class DaprStateError(DaprError):
    """Exception raised when a state operation fails.

    This error occurs when reading, writing, or deleting state fails.
    """

    def __init__(
        self,
        message: str = "State operation failed",
        store_name: str | None = None,
        key: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize DaprStateError.

        Args:
            message: Error message describing the state operation failure.
            store_name: The name of the state store.
            key: The key that was being accessed.
            details: Optional dictionary with state operation details.
        """
        super().__init__(message, details)
        self.store_name = store_name
        self.key = key


class DaprPubSubError(DaprError):
    """Exception raised when a pub/sub operation fails.

    This error occurs when publishing or subscribing to topics fails.
    """

    def __init__(
        self,
        message: str = "Pub/sub operation failed",
        pubsub_name: str | None = None,
        topic: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize DaprPubSubError.

        Args:
            message: Error message describing the pub/sub failure.
            pubsub_name: The name of the pub/sub component.
            topic: The topic that was being accessed.
            details: Optional dictionary with pub/sub operation details.
        """
        super().__init__(message, details)
        self.pubsub_name = pubsub_name
        self.topic = topic


__all__ = [
    "DaprConnectionError",
    "DaprError",
    "DaprInvocationError",
    "DaprPubSubError",
    "DaprStateError",
    "DaprTimeoutError",
]
