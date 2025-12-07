"""User repository interface.

Contains the repository contract for user aggregate.

**Feature: domain-restructuring-2025**
"""

from domain.users.repositories.repositories import IUserReadRepository, IUserRepository

__all__ = [
    "IUserReadRepository",
    "IUserRepository",
]
