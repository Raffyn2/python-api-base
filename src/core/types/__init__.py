"""Core type definitions using PEP 593 Annotated types and PEP 695 type aliases.

Organized into subpackages by category:
- identity/: ID types (ULID, UUID, UUID7, EntityId)
- data/: JSON, numeric, and string types
- patterns/: Result pattern and callback types
- domain/: Repository and security types
- aliases: PEP 695 type aliases (AsyncResult, Handler, Validator, Filter)

**Feature: core-types-split-2025**
**Feature: python-api-base-2025-validation**

Provides reusable type aliases with built-in validation constraints.
Refactored from monolithic types.py into focused modules.
"""

# ID Types
# PEP 695 Type Aliases (Python 3.12+)
from core.types.aliases import (
    AsyncFactory,
    AsyncFilter,
    AsyncHandler,
    AsyncMapper,
    AsyncResult,
    AsyncValidator,
    Callback,
    Factory,
    Filter,
    Handler,
    Mapper,
    Predicate,
    SyncHandler,
    Validator,
    ValidatorWithError,
    VoidAsyncCallback,
)

# JSON Type Aliases
from core.types.data import (
    # String Types
    Email,
    FilterDict,
    Headers,
    HttpUrl,
    ISODateStr,
    JSONArray,
    JSONObject,
    JSONPrimitive,
    JSONValue,
    LongStr,
    MediumStr,
    NonEmptyStr,
    # Numeric Types
    NonNegativeFloat,
    NonNegativeInt,
    PageNumber,
    PageSize,
    Percentage,
    PercentageRange,
    PhoneNumber,
    PositiveFloat,
    PositiveInt,
    QueryParams,
    ShortStr,
    Slug,
    SortOrder,
    TrimmedStr,
    URLPath,
    VersionStr,
)

# Repository/UseCase Type Aliases
from core.types.domain import (
    ApiResult,
    CRUDRepository,
    ErrorResult,
    # Security Types
    JWTToken,
    PaginatedResult,
    Password,
    ReadOnlyRepository,
    ReadOnlyUseCase,
    SecurePassword,
    StandardUseCase,
    WriteOnlyRepository,
)
from core.types.identity import ULID, UUID, UUID7

# Result Pattern and Callback Type Aliases
from core.types.patterns import (
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

__all__ = [
    # ID Types
    "ULID",
    "UUID",
    "UUID7",
    # Repository/UseCase Type Aliases
    "ApiResult",
    # Result Pattern Type Aliases
    "AsyncCallback",
    # PEP 695 Type Aliases (Python 3.12+)
    "AsyncFactory",
    "AsyncFilter",
    "AsyncHandler",
    "AsyncMapper",
    "AsyncResult",
    "AsyncValidator",
    "CRUDRepository",
    "Callback",
    "CompositeSpec",
    # String Types
    "Email",
    "EntityId",
    "ErrorResult",
    "EventCallback",
    "Factory",
    "Failure",
    "Filter",
    # Filter/Query Type Aliases
    "FilterDict",
    "Handler",
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
    "Mapper",
    "MediumStr",
    "Middleware",
    "NonEmptyStr",
    # Numeric Types
    "NonNegativeFloat",
    "NonNegativeInt",
    "OperationResult",
    "PageNumber",
    "PageSize",
    "PaginatedResult",
    "Password",
    "Percentage",
    "PercentageRange",
    "PhoneNumber",
    "PositiveFloat",
    "PositiveInt",
    "Predicate",
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
    "SyncHandler",
    "Timestamp",
    "TrimmedStr",
    "URLPath",
    "Validator",
    "ValidatorWithError",
    "VersionStr",
    "VoidAsyncCallback",
    "VoidResult",
    "WriteOnlyRepository",
]
