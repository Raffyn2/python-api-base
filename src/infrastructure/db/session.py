"""Database session compatibility module.

Re-exports from infrastructure.db.core.session for backward compatibility.

**Feature: infrastructure-restructuring-2025**
"""

from infrastructure.db.core.session import (
    DatabaseSession,
    close_database,
    get_async_session,
    get_database_session,
    init_database,
)

__all__ = [
    "DatabaseSession",
    "close_database",
    "get_async_session",
    "get_database_session",
    "init_database",
]
