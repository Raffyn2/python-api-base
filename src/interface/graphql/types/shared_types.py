"""Shared GraphQL types.

**Feature: interface-modules-workflow-analysis**
"""

import strawberry


@strawberry.type
class PageInfoType:
    """Relay-style pagination info."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None


@strawberry.type
class MutationResult:
    """Generic mutation result."""

    success: bool
    message: str | None = None


def create_empty_page_info() -> PageInfoType:
    """Create empty PageInfoType for error cases."""
    return PageInfoType(
        has_next_page=False,
        has_previous_page=False,
        start_cursor=None,
        end_cursor=None,
    )
