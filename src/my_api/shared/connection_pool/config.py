"""connection_pool configuration."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
from pydantic import BaseModel
from .enums import ConnectionState
from .models import ConnectionInfo


@dataclass
class PoolConfig:
    """Connection pool configuration.

    Attributes:
        min_size: Minimum pool size.
        max_size: Maximum pool size.
        max_idle_time: Max time connection can be idle (seconds).
        health_check_interval: Interval between health checks (seconds).
        acquire_timeout: Timeout for acquiring connection (seconds).
        max_lifetime: Maximum connection lifetime (seconds).
        retry_attempts: Number of retry attempts for failed connections.
    """

    min_size: int = 5
    max_size: int = 20
    max_idle_time: int = 300
    health_check_interval: int = 30
    acquire_timeout: float = 10.0
    max_lifetime: int = 3600
    retry_attempts: int = 3
