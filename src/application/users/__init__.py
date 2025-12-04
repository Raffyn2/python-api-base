"""Users bounded context - Application Layer.

Provides CQRS handlers for User aggregate:
- Commands: Create, update, deactivate users
- Queries: Get, list, search users
- Projections: Event handlers for read model
- Read Model: Query-optimized DTOs

**Architecture: Vertical Slice - Users Bounded Context**
**Feature: architecture-restructuring-2025**
"""

from .commands import CreateUserCommand, CreateUserHandler
from .commands.dtos import (
    ChangeEmailDTO,
    ChangePasswordDTO,
    CreateUserDTO,
    UpdateUserDTO,
    UserDTO,
    UserListDTO,
)
from .commands.mapper import UserMapper
from .queries import (
    GetUserByEmailHandler,
    GetUserByEmailQuery,
    GetUserByIdHandler,
    GetUserByIdQuery,
)
from .read_model import UserListReadDTO, UserReadDTO, UserSearchResultDTO
from .read_model.projections import UserProjectionHandler, UserReadModelProjector

__all__ = [
    # Commands
    "CreateUserCommand",
    "CreateUserHandler",
    # Queries
    "GetUserByIdQuery",
    "GetUserByEmailQuery",
    "GetUserByIdHandler",
    "GetUserByEmailHandler",
    # Write Model DTOs
    "UserDTO",
    "CreateUserDTO",
    "UpdateUserDTO",
    "ChangePasswordDTO",
    "ChangeEmailDTO",
    "UserListDTO",
    # Mappers
    "UserMapper",
    # Projections
    "UserProjectionHandler",
    "UserReadModelProjector",
    # Read Model DTOs
    "UserReadDTO",
    "UserListReadDTO",
    "UserSearchResultDTO",
]
