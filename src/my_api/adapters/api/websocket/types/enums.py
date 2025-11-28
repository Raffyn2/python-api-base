"""types enums."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Standard WebSocket message types."""

    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    BROADCAST = "broadcast"
