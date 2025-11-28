"""feature_flags models."""

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from pydantic import BaseModel
from .enums import FlagStatus, RolloutStrategy


@dataclass
class EvaluationContext:
    """Context for flag evaluation.

    Attributes:
        user_id: Current user ID.
        groups: User's groups.
        attributes: Additional attributes.
    """

    user_id: str | None = None
    groups: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
