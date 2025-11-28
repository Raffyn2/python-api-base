"""memory_profiler models."""

import gc
import sys
import tracemalloc
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .enums import MemoryAlertSeverity, MemoryAlertType


@dataclass
class MemoryAlert:
    """A memory-related alert."""

    alert_type: MemoryAlertType
    severity: MemoryAlertSeverity
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class AllocationInfo:
    """Information about a memory allocation."""

    size_bytes: int
    count: int
    traceback: list[str]

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)
