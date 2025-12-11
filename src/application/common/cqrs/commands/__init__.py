"""CQRS Command infrastructure.

Provides command base class and command bus for write operations.

**Feature: python-api-base-2025-state-of-art**
**Refactored: 2025 - Renamed CommandHandler to CommandHandlerFunc for clarity**
"""

from application.common.cqrs.commands.command_bus import (
    Command,
    CommandBus,
    CommandHandlerFunc,
    MiddlewareFunc,
)

# Backward compatibility alias
CommandHandler = CommandHandlerFunc

__all__ = [
    "Command",
    "CommandBus",
    "CommandHandler",  # Alias for backward compatibility
    "CommandHandlerFunc",
    "MiddlewareFunc",
]
