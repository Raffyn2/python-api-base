"""Users bounded context.

Organized into subpackages by responsibility:
- aggregates/: User aggregate root
- events/: Domain events
- repositories/: Repository interface
- services/: Domain services
- value_objects/: Value objects

**Feature: domain-restructuring-2025**
"""

from domain.users.aggregates import UserAggregate
from domain.users.events import (
    UserDeactivatedEvent,
    UserEmailChangedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPasswordChangedEvent,
    UserProfileUpdatedEvent,
    UserReactivatedEvent,
    UserRegisteredEvent,
)
from domain.users.repositories import IUserReadRepository, IUserRepository
from domain.users.services import UserDomainService
from domain.users.value_objects import Email, PasswordHash, PhoneNumber, UserId, Username

__all__ = [
    # Value Objects
    "Email",
    # Repositories
    "IUserReadRepository",
    "IUserRepository",
    "PasswordHash",
    "PhoneNumber",
    # Aggregate
    "UserAggregate",
    # Events
    "UserDeactivatedEvent",
    # Services
    "UserDomainService",
    "UserEmailChangedEvent",
    "UserEmailVerifiedEvent",
    "UserId",
    "UserLoggedInEvent",
    "UserPasswordChangedEvent",
    "UserProfileUpdatedEvent",
    "UserReactivatedEvent",
    "UserRegisteredEvent",
    "Username",
]
