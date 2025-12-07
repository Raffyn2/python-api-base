"""User domain events.

Contains domain events for user aggregate.

**Feature: domain-restructuring-2025**
"""

from domain.users.events.events import (
    UserDeactivatedEvent,
    UserEmailChangedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPasswordChangedEvent,
    UserProfileUpdatedEvent,
    UserReactivatedEvent,
    UserRegisteredEvent,
)

__all__ = [
    "UserDeactivatedEvent",
    "UserEmailChangedEvent",
    "UserEmailVerifiedEvent",
    "UserLoggedInEvent",
    "UserPasswordChangedEvent",
    "UserProfileUpdatedEvent",
    "UserReactivatedEvent",
    "UserRegisteredEvent",
]
