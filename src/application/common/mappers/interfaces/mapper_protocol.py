"""Mapper protocol definition.

**Feature: application-layer-code-review-2025**
**Refactored: Split from mapper.py for one-class-per-file compliance**

Re-exports Mapper protocol from core.protocols.application for consistency.
The canonical implementation is in core.protocols.application.Mapper.
"""

# Re-export from canonical location (Single Source of Truth)
from core.protocols.application import Mapper

__all__ = ["Mapper"]
