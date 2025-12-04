"""Users bounded context.

**Feature: architecture-restructuring-2025**
"""

from domain.users.aggregates import UserAggregate
from domain.users.events import (
    UserDeactivatedEvent,
    UserEmailChangedEvent,
    UserRegisteredEvent,
)
from domain.users.repositories import IUserRepository
from domain.users.value_objects import Email, PasswordHash, UserId, Username

__all__ = [
    "Email",
    "IUserRepository",
    "PasswordHash",
    "UserAggregate",
    "UserDeactivatedEvent",
    "UserEmailChangedEvent",
    "UserId",
    "UserRegisteredEvent",
    "Username",
]
