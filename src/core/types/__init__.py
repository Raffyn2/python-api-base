"""Core type definitions using PEP 593 Annotated types and PEP 695 type aliases.

**Feature: core-types-split-2025**

Provides reusable type aliases with built-in validation constraints.
Refactored from monolithic types.py into focused modules.
"""

# ID Types
from core.types.id_types import ULID, UUID

# JSON Type Aliases
from core.types.json_types import (
    FilterDict,
    Headers,
    JSONArray,
    JSONObject,
    JSONPrimitive,
    JSONValue,
    QueryParams,
    SortOrder,
)

# Numeric Types
from core.types.numeric_types import (
    NonNegativeFloat,
    NonNegativeInt,
    PageNumber,
    PageSize,
    Percentage,
    PositiveFloat,
    PositiveInt,
)

# Repository/UseCase Type Aliases
from core.types.repository_types import (
    ApiResult,
    CRUDRepository,
    ErrorResult,
    PaginatedResult,
    ReadOnlyRepository,
    ReadOnlyUseCase,
    StandardUseCase,
    WriteOnlyRepository,
)

# Result Pattern and Callback Type Aliases
from core.types.result_types import (
    AsyncCallback,
    CompositeSpec,
    EntityId,
    EventCallback,
    Failure,
    Middleware,
    OperationResult,
    Spec,
    Success,
    SyncCallback,
    Timestamp,
    VoidResult,
)

# Security Types
from core.types.security_types import JWTToken, Password, SecurePassword

# String Types
from core.types.string_types import (
    Email,
    HttpUrl,
    ISODateStr,
    LongStr,
    MediumStr,
    NonEmptyStr,
    PhoneNumber,
    ShortStr,
    Slug,
    TrimmedStr,
    VersionStr,
)

__all__ = [
    # ID Types
    "ULID",
    "UUID",
    # Response Type Aliases
    "ApiResult",
    # Callback Type Aliases
    "AsyncCallback",
    # Repository/UseCase Type Aliases
    "CRUDRepository",
    # Other
    "CompositeSpec",
    # String Types
    "Email",
    "EntityId",
    "ErrorResult",
    "EventCallback",
    # Result Pattern Type Aliases
    "Failure",
    # Filter/Query Type Aliases
    "FilterDict",
    "Headers",
    "HttpUrl",
    "ISODateStr",
    # JSON Type Aliases
    "JSONArray",
    "JSONObject",
    "JSONPrimitive",
    "JSONValue",
    # Security Types
    "JWTToken",
    "LongStr",
    "MediumStr",
    "Middleware",
    "NonEmptyStr",
    # Numeric Types
    "NonNegativeFloat",
    "NonNegativeInt",
    "OperationResult",
    # Pagination Types
    "PageNumber",
    "PageSize",
    "PaginatedResult",
    "Password",
    "Percentage",
    "PhoneNumber",
    "PositiveFloat",
    "PositiveInt",
    "QueryParams",
    "ReadOnlyRepository",
    "ReadOnlyUseCase",
    "SecurePassword",
    "ShortStr",
    "Slug",
    "SortOrder",
    "Spec",
    "StandardUseCase",
    "Success",
    "SyncCallback",
    "Timestamp",
    "TrimmedStr",
    "VersionStr",
    "VoidResult",
    "WriteOnlyRepository",
]
