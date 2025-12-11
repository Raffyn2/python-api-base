"""User DTOs (Data Transfer Objects).

Organized by context:
- commands: Command request/response DTOs
- read_model: Read model DTOs

**Feature: architecture-restructuring-2025**
"""

from application.users.dtos.commands import (
    ChangeEmailDTO,
    ChangePasswordDTO,
    CreateUserDTO,
    UpdateUserDTO,
    UserDTO,
    UserListDTO,
)
from application.users.dtos.read_model import (
    UserActivityReadDTO,
    UserListReadDTO,
    UserReadDTO,
    UserSearchResultDTO,
)

__all__ = [
    "ChangeEmailDTO",
    "ChangePasswordDTO",
    "CreateUserDTO",
    "UpdateUserDTO",
    "UserActivityReadDTO",
    # Commands
    "UserDTO",
    "UserListDTO",
    "UserListReadDTO",
    # Read Model
    "UserReadDTO",
    "UserSearchResultDTO",
]
