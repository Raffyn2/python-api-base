"""Entity trait protocols.

Defines fundamental protocols for common entity characteristics like
identification, timestamps, and soft deletion support.

**Feature: core-protocols-restructuring-2025**
"""

from core.protocols.entity.base import Identifiable, Named, SoftDeletable, Timestamped

__all__ = [
    "Identifiable",
    "Named",
    "SoftDeletable",
    "Timestamped",
]
