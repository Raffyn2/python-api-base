"""Relay Connection specification types.

This module re-exports Strawberry types from shared_types for consistency.
The actual Relay types used in the project are Strawberry-based.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 20.2**

Note: Generic dataclass versions were removed as they duplicated
Strawberry types in types/shared_types.py and types/*_types.py.
"""

from interface.graphql.types.shared_types import PageInfoType

# Re-export for backward compatibility
PageInfo = PageInfoType

__all__ = ["PageInfo", "PageInfoType"]
