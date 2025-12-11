"""Design patterns base classes.

**Feature: architecture-restructuring-2025**
"""

from core.base.patterns.pagination import CursorPage, CursorPagination
from core.base.patterns.result import (
    Err,
    Ok,
    Result,
    collect_results,
    err,
    ok,
    result_from_dict,
    try_catch,
    try_catch_async,
)
from core.base.patterns.specification import (
    AndSpecification,
    AttributeSpecification,
    CompositeSpecification,
    FalseSpecification,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
    Specification,
    TrueSpecification,
    spec,
)
from core.base.patterns.uow import UnitOfWork
from core.base.patterns.use_case import BaseUseCase, IMapper, IRepository
from core.base.patterns.validation import (
    AlternativeValidator,
    ChainedValidator,
    CompositeValidator,
    FieldError,
    NotEmptyValidator,
    PredicateValidator,
    RangeValidator,
    ValidationError,
    Validator,
    validate_all,
)

__all__ = [
    "AlternativeValidator",
    "AndSpecification",
    "AttributeSpecification",
    # UseCase
    "BaseUseCase",
    "ChainedValidator",
    "CompositeSpecification",
    "CompositeValidator",
    # Pagination
    "CursorPage",
    "CursorPagination",
    "Err",
    "FalseSpecification",
    # Validation
    "FieldError",
    "IMapper",
    "IRepository",
    "NotEmptyValidator",
    "NotSpecification",
    # Result
    "Ok",
    "OrSpecification",
    "PredicateSpecification",
    "PredicateValidator",
    "RangeValidator",
    "Result",
    # Specification
    "Specification",
    "TrueSpecification",
    # UoW
    "UnitOfWork",
    "ValidationError",
    "Validator",
    "collect_results",
    "err",
    "ok",
    "result_from_dict",
    "spec",
    "try_catch",
    "try_catch_async",
    "validate_all",
]
