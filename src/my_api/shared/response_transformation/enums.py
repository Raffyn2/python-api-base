"""response_transformation enums."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Generic, TypeVar


class TransformationType(Enum):
    """Types of transformations."""

    FIELD_RENAME = "field_rename"
    FIELD_REMOVE = "field_remove"
    FIELD_ADD = "field_add"
    FIELD_TRANSFORM = "field_transform"
    STRUCTURE_CHANGE = "structure_change"
    FORMAT_CHANGE = "format_change"
