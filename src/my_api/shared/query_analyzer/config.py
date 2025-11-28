"""query_analyzer configuration."""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel
from .enums import QueryType, OptimizationSuggestion
from .models import QueryMetrics, IndexSuggestion


@dataclass
class AnalyzerConfig:
    """Query analyzer configuration.

    Attributes:
        slow_query_threshold_ms: Threshold for slow queries.
        max_queries_stored: Maximum queries to store.
        enable_explain: Whether to run EXPLAIN.
        sample_rate: Query sampling rate (0.0-1.0).
    """

    slow_query_threshold_ms: float = 100.0
    max_queries_stored: int = 1000
    enable_explain: bool = True
    sample_rate: float = 1.0
