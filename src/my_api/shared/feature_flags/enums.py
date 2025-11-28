"""feature_flags enums."""

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from pydantic import BaseModel


class FlagStatus(str, Enum):
    """Feature flag status."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    PERCENTAGE = "percentage"
    TARGETED = "targeted"

class RolloutStrategy(str, Enum):
    """Rollout strategy types."""

    ALL = "all"
    NONE = "none"
    PERCENTAGE = "percentage"
    USER_IDS = "user_ids"
    GROUPS = "groups"
    CUSTOM = "custom"
