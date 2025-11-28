"""streaming enums."""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Generic, TypeVar
from pydantic import BaseModel


class StreamFormat(str, Enum):
    """Stream output formats."""

    JSON_LINES = "json_lines"  # Newline-delimited JSON
    SSE = "sse"  # Server-Sent Events
    CHUNKED = "chunked"  # Raw chunked transfer
