"""Base mapper with common list operations.

**Feature: mapper-consolidation-2025**

Eliminates code duplication across mappers by providing
common list conversion methods in a reusable base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeVar

TEntity = TypeVar("TEntity")
TDto = TypeVar("TDto")


class BaseMapper(ABC):
    """Base mapper with common list operations.

    Provides default implementations for list conversions
    to eliminate code duplication across concrete mappers.

    Subclasses only need to implement:
    - to_dto(entity) -> dto
    - to_entity(dto) -> entity

    The list methods (to_dto_list, to_entity_list) are
    automatically available.

    Example:
        >>> class UserMapper(BaseMapper[User, UserDTO]):
        ...     def to_dto(self, entity: User) -> UserDTO:
        ...         return UserDTO(id=entity.id, name=entity.name)
        ...
        ...     def to_entity(self, dto: UserDTO) -> User:
        ...         return User(id=dto.id, name=dto.name)
        ...
        >>> mapper = UserMapper()
        >>> users = [user1, user2, user3]
        >>> dtos = mapper.to_dto_list(users)  # Already implemented!
    """

    @abstractmethod
    def to_dto(self, entity: TEntity) -> TDto:
        """Convert entity to DTO.

        Must be implemented by subclasses.

        Args:
            entity: Domain entity to convert.

        Returns:
            DTO representation of the entity.
        """
        ...

    @abstractmethod
    def to_entity(self, dto: TDto) -> TEntity:
        """Convert DTO to entity.

        Must be implemented by subclasses.

        Args:
            dto: DTO to convert.

        Returns:
            Domain entity representation.
        """
        ...

    def to_dto_list(self, entities: Sequence[TEntity]) -> list[TDto]:
        """Convert list of entities to DTOs.

        This method is implemented by the base class
        to avoid duplication in every mapper.

        Args:
            entities: Sequence of domain entities.

        Returns:
            List of DTOs.
        """
        return [self.to_dto(entity) for entity in entities]

    def to_entity_list(self, dtos: Sequence[TDto]) -> list[TEntity]:
        """Convert list of DTOs to entities.

        This method is implemented by the base class
        to avoid duplication in every mapper.

        Args:
            dtos: Sequence of DTOs.

        Returns:
            List of domain entities.
        """
        return [self.to_entity(dto) for dto in dtos]

    # Aliases for compatibility with existing code
    def to_response(self, entity: TEntity) -> TDto:
        """Alias for to_dto for backward compatibility."""
        return self.to_dto(entity)

    def to_response_list(self, entities: Sequence[TEntity]) -> list[TDto]:
        """Alias for to_dto_list for backward compatibility."""
        return self.to_dto_list(entities)
