"""bff enums."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, Protocol, TypeVar, runtime_checkable


class ClientType(Enum):
    """Supported client types."""

    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    API = "api"
    UNKNOWN = "unknown"
