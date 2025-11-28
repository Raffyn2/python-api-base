"""graphql_federation enums."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class FederationDirective(str, Enum):
    """Apollo Federation directives."""

    KEY = "@key"
    EXTERNAL = "@external"
    REQUIRES = "@requires"
    PROVIDES = "@provides"
    EXTENDS = "@extends"
    SHAREABLE = "@shareable"
    INACCESSIBLE = "@inaccessible"
    OVERRIDE = "@override"
    TAG = "@tag"
