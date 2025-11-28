"""streaming configuration."""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Generic, TypeVar
from pydantic import BaseModel
from .enums import StreamFormat
from .models import SSEEvent


@dataclass
class StreamConfig:
    """Streaming configuration.

    Attributes:
        format: Output format.
        chunk_size: Size of chunks in bytes.
        flush_interval_ms: Interval between flushes in milliseconds.
        heartbeat_interval_ms: SSE heartbeat interval.
        max_buffer_size: Maximum buffer size before flush.
    """

    format: StreamFormat = StreamFormat.JSON_LINES
    chunk_size: int = 8192
    flush_interval_ms: int = 100
    heartbeat_interval_ms: int = 15000
    max_buffer_size: int = 65536
