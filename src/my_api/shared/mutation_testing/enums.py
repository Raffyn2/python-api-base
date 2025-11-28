"""mutation_testing enums."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import json
import hashlib


class MutantStatus(Enum):
    """Status of a mutant."""

    KILLED = "killed"
    SURVIVED = "survived"
    TIMEOUT = "timeout"
    SUSPICIOUS = "suspicious"
    SKIPPED = "skipped"
    INCOMPETENT = "incompetent"

class MutationOperator(Enum):
    """Standard mutation operators."""

    AOR = "arithmetic_operator_replacement"
    ROR = "relational_operator_replacement"
    COR = "conditional_operator_replacement"
    LCR = "logical_connector_replacement"
    ASR = "assignment_operator_replacement"
    UOI = "unary_operator_insertion"
    SDL = "statement_deletion"
    SVR = "scalar_variable_replacement"
