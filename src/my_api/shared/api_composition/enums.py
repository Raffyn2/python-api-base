"""api_composition enums."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, TypeVar


class ExecutionStrategy(Enum):
    """Execution strategies for API composition."""

    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    PARALLEL_WITH_FALLBACK = "parallel_with_fallback"

class CompositionStatus(Enum):
    """Status of a composition operation."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"  # Some calls succeeded
    FAILED = "failed"
