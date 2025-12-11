"""Pydantic V2 performance optimizations.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

Implements:
- TypeAdapter for high-performance validation
- model_validate_json for direct JSON parsing
- computed_field for derived properties
- Reusable validators with caching
"""

from collections.abc import Sequence
from functools import lru_cache
from typing import Annotated, Any, Self, TypeVar

from pydantic import BaseModel, TypeAdapter, computed_field
from pydantic.functional_validators import BeforeValidator

T = TypeVar("T", bound=BaseModel)


class TypeAdapterCache[T: BaseModel]:
    """Cached TypeAdapter for high-performance validation.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.1**

    TypeAdapter instances are expensive to create. This class
    caches them for reuse across multiple validation calls.

    Example:
        >>> adapter = TypeAdapterCache[UserDTO]()
        >>> user = adapter.validate_json(b'{"name": "John", "email": "john@example.com"}')
        >>> users = adapter.validate_list_json(b'[{"name": "John"}, {"name": "Jane"}]')
    """

    _adapter: TypeAdapter[T] | None = None
    _list_adapter: TypeAdapter[list[T]] | None = None

    def __init__(self, model_type: type[T]) -> None:
        """Initialize with model type.

        Args:
            model_type: Pydantic model class.
        """
        self._model_type = model_type

    @property
    def adapter(self) -> TypeAdapter[T]:
        """Get or create TypeAdapter for single items."""
        if self._adapter is None:
            self._adapter = TypeAdapter(self._model_type)
        return self._adapter

    @property
    def list_adapter(self) -> TypeAdapter[list[T]]:
        """Get or create TypeAdapter for lists."""
        if self._list_adapter is None:
            self._list_adapter = TypeAdapter(list[self._model_type])
        return self._list_adapter

    def validate_json(self, data: bytes | str) -> T:
        """Validate JSON directly to model.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.2**

        Uses model_validate_json for ~2x performance vs json.loads + validate.

        Args:
            data: JSON bytes or string.

        Returns:
            Validated model instance.
        """
        return self.adapter.validate_json(data)

    def validate_list_json(self, data: bytes | str) -> list[T]:
        """Validate JSON array directly to list of models.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.2**

        Args:
            data: JSON bytes or string containing array.

        Returns:
            List of validated model instances.
        """
        return self.list_adapter.validate_json(data)

    def validate_python(self, data: dict[str, Any]) -> T:
        """Validate Python dict to model.

        Args:
            data: Dictionary of field values.

        Returns:
            Validated model instance.
        """
        return self.adapter.validate_python(data)

    def dump_json(self, instance: T) -> bytes:
        """Serialize model to JSON bytes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.3**

        Args:
            instance: Model instance.

        Returns:
            JSON bytes.
        """
        return self.adapter.dump_json(instance)

    def dump_json_list(self, instances: Sequence[T]) -> bytes:
        """Serialize list of models to JSON bytes.

        Args:
            instances: Sequence of model instances.

        Returns:
            JSON bytes.
        """
        return self.list_adapter.dump_json(list(instances))


@lru_cache(maxsize=128)
def get_type_adapter[T: BaseModel](model_type: type[T]) -> TypeAdapter[T]:
    """Get cached TypeAdapter for a model type.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.1**

    Args:
        model_type: Pydantic model class.

    Returns:
        Cached TypeAdapter instance.
    """
    return TypeAdapter(model_type)


def validate_json_fast[T: BaseModel](model_type: type[T], data: bytes | str) -> T:
    """Fast JSON validation using cached TypeAdapter.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.2**

    Args:
        model_type: Pydantic model class.
        data: JSON bytes or string.

    Returns:
        Validated model instance.
    """
    adapter = get_type_adapter(model_type)
    return adapter.validate_json(data)


# === Common Validators ===


def strip_whitespace(v: str) -> str:
    """Strip whitespace from string."""
    return v.strip() if isinstance(v, str) else v


def lowercase(v: str) -> str:
    """Convert string to lowercase."""
    return v.lower() if isinstance(v, str) else v


def uppercase(v: str) -> str:
    """Convert string to uppercase."""
    return v.upper() if isinstance(v, str) else v


# Annotated types with validators
StrippedStr = Annotated[str, BeforeValidator(strip_whitespace)]
LowercaseStr = Annotated[str, BeforeValidator(lowercase)]
UppercaseStr = Annotated[str, BeforeValidator(uppercase)]
EmailStr = Annotated[str, BeforeValidator(strip_whitespace), BeforeValidator(lowercase)]


# === Example Models with Pydantic V2 Features ===


class OptimizedBaseModel(BaseModel):
    """Base model with Pydantic V2 optimizations.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.4**
    """

    model_config = {
        # Validate on assignment for safety
        "validate_assignment": True,
        # Use enum values instead of enum objects
        "use_enum_values": True,
        # Faster JSON serialization
        "ser_json_bytes": "utf8",
        # Extra fields handling
        "extra": "forbid",
    }

    def to_json_bytes(self) -> bytes:
        """Serialize to JSON bytes efficiently.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.3**
        """
        return self.model_dump_json().encode()

    @classmethod
    def from_json_bytes(cls, data: bytes | str) -> Self:
        """Parse from JSON bytes efficiently.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.2**
        """
        return cls.model_validate_json(data)


class ComputedFieldExample(BaseModel):
    """Example model demonstrating computed_field.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.5**
    """

    first_name: str
    last_name: str
    price: float
    quantity: int

    @computed_field
    @property
    def full_name(self) -> str:
        """Computed full name from first and last name."""
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def total(self) -> float:
        """Computed total from price and quantity."""
        return self.price * self.quantity


# === Bulk Validation Utilities ===


def validate_bulk[T: BaseModel](
    model_type: type[T],
    items: Sequence[dict[str, Any]],
    *,
    strict: bool = False,
) -> tuple[list[T], list[tuple[int, Exception]]]:
    """Validate multiple items, collecting errors.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.4**

    Args:
        model_type: Pydantic model class.
        items: Sequence of dictionaries to validate.
        strict: If True, use strict validation.

    Returns:
        Tuple of (valid_items, errors) where errors is list of (index, exception).
    """
    adapter = get_type_adapter(model_type)
    valid: list[T] = []
    errors: list[tuple[int, Exception]] = []

    for i, item in enumerate(items):
        try:
            validated = adapter.validate_python(item, strict=strict)
            valid.append(validated)
        except Exception as e:
            errors.append((i, e))

    return valid, errors


def validate_bulk_json[T: BaseModel](
    model_type: type[T],
    json_data: bytes | str,
) -> list[T]:
    """Validate JSON array to list of models.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.2**

    Args:
        model_type: Pydantic model class.
        json_data: JSON bytes or string containing array.

    Returns:
        List of validated model instances.
    """
    list_adapter = TypeAdapter(list[model_type])
    return list_adapter.validate_json(json_data)
