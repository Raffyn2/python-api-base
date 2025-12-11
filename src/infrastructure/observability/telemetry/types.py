"""Type definitions for telemetry module.

**Feature: enterprise-generics-2025**
**Improvement: P1-1 - Replace Any with OpenTelemetry-compliant types**

Type definitions matching OpenTelemetry specification for better type safety
while maintaining compatibility with no-op implementations.
"""

from __future__ import annotations

from collections.abc import Sequence

# OpenTelemetry attribute value types per specification
type AttributePrimitive = str | bool | int | float
type AttributeSequence = Sequence[str] | Sequence[bool] | Sequence[int] | Sequence[float]
type AttributeValue = AttributePrimitive | AttributeSequence
type Attributes = dict[str, AttributeValue]

__all__ = [
    "AttributePrimitive",
    "AttributeSequence",
    "AttributeValue",
    "Attributes",
]
