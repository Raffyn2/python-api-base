"""connection_pool enums."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
from pydantic import BaseModel


class ConnectionState(str, Enum):
    """Connection state."""

    IDLE = "idle"
    IN_USE = "in_use"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"
