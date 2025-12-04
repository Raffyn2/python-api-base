"""Type definitions for HTTP client module.

**Feature: enterprise-generics-2025**
**Improvement: P1-1 - Replace Any with specific JSON types**
"""

from __future__ import annotations

# JSON type definitions using PEP 695 syntax
type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | JsonObject | JsonArray
type JsonObject = dict[str, JsonValue]
type JsonArray = list[JsonValue]

__all__ = [
    "JsonArray",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
]
