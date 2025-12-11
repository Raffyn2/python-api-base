"""Pattern type definitions.

Contains Result pattern types and related type aliases.

**Feature: core-types-restructuring-2025**
"""

from core.types.identity import EntityId
from core.types.patterns.result_types import (
    AsyncCallback,
    CompositeSpec,
    EventCallback,
    Failure,
    Middleware,
    OperationResult,
    Spec,
    Success,
    SyncCallback,
    Timestamp,
    VoidResult,
)

__all__ = [
    "AsyncCallback",
    "CompositeSpec",
    "EntityId",
    "EventCallback",
    "Failure",
    "Middleware",
    "OperationResult",
    "Spec",
    "Success",
    "SyncCallback",
    "Timestamp",
    "VoidResult",
]
