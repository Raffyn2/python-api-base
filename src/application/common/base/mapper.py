"""Generic Mapper for entity-DTO conversion.

Provides type-safe mapping between entities and DTOs.
Uses PEP 695 type parameter syntax.

**Feature: application-layer-code-review-2025**
**Refactored: Split into separate files for one-class-per-file compliance**
**Backward Compatibility: This module re-exports all classes for existing imports**
"""

# Re-export all mapper classes for backward compatibility
from application.common.base.auto_mapper import AutoMapper
from application.common.base.generic_mapper import GenericMapper
from application.common.base.mapper_error import MapperError
from application.common.base.mapper_interface import IMapper
from application.common.base.mapper_protocol import Mapper

__all__ = [
    "AutoMapper",
    "GenericMapper",
    "IMapper",
    "Mapper",
    "MapperError",
]
