"""GraphQL Relay support.

Contains Relay cursor-based pagination utilities.
Actual Relay types (Connection, Edge) are defined per-entity in types/.

**Feature: interface-restructuring-2025**
"""

from interface.graphql.relay.relay import PageInfo, PageInfoType

__all__ = [
    "PageInfo",
    "PageInfoType",
]
