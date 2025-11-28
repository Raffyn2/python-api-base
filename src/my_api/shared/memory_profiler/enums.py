"""memory_profiler enums."""

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


class MemoryAlertSeverity(Enum):
    """Severity levels for memory alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class MemoryAlertType(Enum):
    """Types of memory alerts."""

    HIGH_USAGE = "high_usage"
    LEAK_DETECTED = "leak_detected"
    GROWTH_RATE = "growth_rate"
    ALLOCATION_SPIKE = "allocation_spike"
    GC_PRESSURE = "gc_pressure"
