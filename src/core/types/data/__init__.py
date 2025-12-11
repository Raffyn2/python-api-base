"""Data type definitions.

Contains JSON, numeric, and string types with validation.

**Feature: core-types-restructuring-2025**
"""

from core.types.data.json_types import (
    FilterDict,
    Headers,
    JSONArray,
    JSONObject,
    JSONPrimitive,
    JSONValue,
    QueryParams,
    SortOrder,
)
from core.types.data.numeric_types import (
    NonNegativeFloat,
    NonNegativeInt,
    PageNumber,
    PageSize,
    Percentage,
    PercentageRange,
    PositiveFloat,
    PositiveInt,
)
from core.types.data.string_types import (
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
    URLPath,
    VersionStr,
)

__all__ = [
    # String Types
    "Email",
    # JSON Types
    "FilterDict",
    "Headers",
    "HttpUrl",
    "ISODateStr",
    "JSONArray",
    "JSONObject",
    "JSONPrimitive",
    "JSONValue",
    "LongStr",
    "MediumStr",
    "NonEmptyStr",
    # Numeric Types
    "NonNegativeFloat",
    "NonNegativeInt",
    "PageNumber",
    "PageSize",
    "Percentage",
    "PercentageRange",
    "PhoneNumber",
    "PositiveFloat",
    "PositiveInt",
    "QueryParams",
    "ShortStr",
    "Slug",
    "SortOrder",
    "TrimmedStr",
    "URLPath",
    "VersionStr",
]
