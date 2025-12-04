"""Property-based tests for Pydantic V2 performance optimizations.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

Property tests for:
- Property 3: TypeAdapter Caching
- Property 4: JSON Validation Performance
"""

import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

from core.shared.validation import (
    TypeAdapterCache,
    get_type_adapter,
    validate_json_fast,
    validate_bulk,
    validate_bulk_json,
    OptimizedBaseModel,
    ComputedFieldExample,
    StrippedStr,
    LowercaseStr,
    UppercaseStr,
)


# === Test Models ===


class SampleDTO(BaseModel):
    """Sample DTO for testing."""

    name: str
    value: int
    active: bool = True


class PersonDTO(BaseModel):
    """Person DTO for testing computed fields."""

    first_name: str
    last_name: str


# === Strategies ===


name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
).filter(lambda x: x.strip() != "")

value_strategy = st.integers(min_value=-1000000, max_value=1000000)

sample_dict_strategy = st.fixed_dictionaries({
    "name": name_strategy,
    "value": value_strategy,
    "active": st.booleans(),
})


# === Property Tests ===


class TestTypeAdapterCaching:
    """Property 3: TypeAdapter Caching.

    TypeAdapter instances SHALL be cached and reused for performance.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.1**
    """

    def test_type_adapter_cached(self) -> None:
        """get_type_adapter SHALL return same instance for same type.

        **Feature: api-best-practices-review-2025, Property 3**
        **Validates: Requirements 3.1**
        """
        adapter1 = get_type_adapter(SampleDTO)
        adapter2 = get_type_adapter(SampleDTO)
        
        # Should be same cached instance
        assert adapter1 is adapter2

    def test_type_adapter_cache_class_reuses_adapter(self) -> None:
        """TypeAdapterCache SHALL reuse adapter instances.

        **Feature: api-best-practices-review-2025, Property 3**
        **Validates: Requirements 3.1**
        """
        cache = TypeAdapterCache(SampleDTO)
        
        adapter1 = cache.adapter
        adapter2 = cache.adapter
        
        assert adapter1 is adapter2

    def test_type_adapter_cache_list_reuses_adapter(self) -> None:
        """TypeAdapterCache SHALL reuse list adapter instances.

        **Feature: api-best-practices-review-2025, Property 3**
        **Validates: Requirements 3.1**
        """
        cache = TypeAdapterCache(SampleDTO)
        
        adapter1 = cache.list_adapter
        adapter2 = cache.list_adapter
        
        assert adapter1 is adapter2


class TestJSONValidationPerformance:
    """Property 4: JSON Validation Performance.

    model_validate_json SHALL correctly parse JSON to models.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.2**
    """

    @settings(max_examples=50, deadline=None)
    @given(data=sample_dict_strategy)
    def test_validate_json_fast_round_trip(self, data: dict[str, Any]) -> None:
        """validate_json_fast SHALL correctly parse valid JSON.

        **Feature: api-best-practices-review-2025, Property 4**
        **Validates: Requirements 3.2**
        """
        json_bytes = json.dumps(data).encode()
        
        result = validate_json_fast(SampleDTO, json_bytes)
        
        assert result.name == data["name"]
        assert result.value == data["value"]
        assert result.active == data["active"]

    @settings(max_examples=50, deadline=None)
    @given(data=sample_dict_strategy)
    def test_type_adapter_cache_json_round_trip(
        self, data: dict[str, Any]
    ) -> None:
        """TypeAdapterCache.validate_json SHALL match dict validation.

        **Feature: api-best-practices-review-2025, Property 4**
        **Validates: Requirements 3.2**
        """
        cache = TypeAdapterCache(SampleDTO)
        json_bytes = json.dumps(data).encode()
        
        from_json = cache.validate_json(json_bytes)
        from_dict = cache.validate_python(data)
        
        assert from_json.name == from_dict.name
        assert from_json.value == from_dict.value
        assert from_json.active == from_dict.active

    @settings(max_examples=20, deadline=None)
    @given(items=st.lists(sample_dict_strategy, min_size=1, max_size=10))
    def test_validate_list_json(self, items: list[dict[str, Any]]) -> None:
        """validate_bulk_json SHALL parse JSON arrays.

        **Feature: api-best-practices-review-2025, Property 4**
        **Validates: Requirements 3.2**
        """
        json_bytes = json.dumps(items).encode()
        
        results = validate_bulk_json(SampleDTO, json_bytes)
        
        assert len(results) == len(items)
        for result, original in zip(results, items):
            assert result.name == original["name"]
            assert result.value == original["value"]


class TestJSONSerialization:
    """Tests for JSON serialization performance.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.3**
    """

    @settings(max_examples=50, deadline=None)
    @given(data=sample_dict_strategy)
    def test_dump_json_round_trip(self, data: dict[str, Any]) -> None:
        """dump_json SHALL produce valid JSON.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.3**
        """
        cache = TypeAdapterCache(SampleDTO)
        
        # Create instance
        instance = cache.validate_python(data)
        
        # Serialize to JSON
        json_bytes = cache.dump_json(instance)
        
        # Parse back
        restored = cache.validate_json(json_bytes)
        
        assert restored.name == instance.name
        assert restored.value == instance.value
        assert restored.active == instance.active

    @settings(max_examples=20, deadline=None)
    @given(items=st.lists(sample_dict_strategy, min_size=1, max_size=10))
    def test_dump_json_list_round_trip(
        self, items: list[dict[str, Any]]
    ) -> None:
        """dump_json_list SHALL produce valid JSON array.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.3**
        """
        cache = TypeAdapterCache(SampleDTO)
        
        # Create instances
        instances = [cache.validate_python(item) for item in items]
        
        # Serialize to JSON
        json_bytes = cache.dump_json_list(instances)
        
        # Parse back
        restored = cache.validate_list_json(json_bytes)
        
        assert len(restored) == len(instances)


class TestBulkValidation:
    """Tests for bulk validation utilities.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.4**
    """

    @settings(max_examples=20, deadline=None)
    @given(items=st.lists(sample_dict_strategy, min_size=1, max_size=10))
    def test_validate_bulk_all_valid(
        self, items: list[dict[str, Any]]
    ) -> None:
        """validate_bulk SHALL return all valid items.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.4**
        """
        valid, errors = validate_bulk(SampleDTO, items)
        
        assert len(valid) == len(items)
        assert len(errors) == 0

    def test_validate_bulk_with_errors(self) -> None:
        """validate_bulk SHALL collect errors separately.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.4**
        """
        items = [
            {"name": "Valid", "value": 100},
            {"name": "Missing value"},  # Invalid - missing required field
            {"name": "Also Valid", "value": 200},
        ]
        
        valid, errors = validate_bulk(SampleDTO, items)
        
        assert len(valid) == 2
        assert len(errors) == 1
        assert errors[0][0] == 1  # Index of invalid item


class TestComputedField:
    """Tests for computed_field functionality.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.5**
    """

    @settings(max_examples=50, deadline=None)
    @given(
        first_name=name_strategy,
        last_name=name_strategy,
        price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False),
        quantity=st.integers(min_value=1, max_value=1000),
    )
    def test_computed_field_calculated(
        self,
        first_name: str,
        last_name: str,
        price: float,
        quantity: int,
    ) -> None:
        """computed_field SHALL calculate derived values.

        **Feature: api-best-practices-review-2025, Property 5**
        **Validates: Requirements 3.5**
        """
        model = ComputedFieldExample(
            first_name=first_name,
            last_name=last_name,
            price=price,
            quantity=quantity,
        )
        
        assert model.full_name == f"{first_name} {last_name}"
        assert model.total == pytest.approx(price * quantity, rel=1e-9)

    def test_computed_field_in_serialization(self) -> None:
        """computed_field SHALL be included in serialization.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.5**
        """
        model = ComputedFieldExample(
            first_name="John",
            last_name="Doe",
            price=10.0,
            quantity=5,
        )
        
        data = model.model_dump()
        
        assert "full_name" in data
        assert data["full_name"] == "John Doe"
        assert "total" in data
        assert data["total"] == 50.0


class TestAnnotatedValidators:
    """Tests for annotated type validators.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.4**
    """

    def test_stripped_str_removes_whitespace(self) -> None:
        """StrippedStr SHALL remove leading/trailing whitespace.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.4**
        """
        class TestModel(BaseModel):
            name: StrippedStr
        
        model = TestModel(name="  hello world  ")
        assert model.name == "hello world"

    def test_lowercase_str_converts(self) -> None:
        """LowercaseStr SHALL convert to lowercase.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.4**
        """
        class TestModel(BaseModel):
            code: LowercaseStr
        
        model = TestModel(code="HELLO")
        assert model.code == "hello"

    def test_uppercase_str_converts(self) -> None:
        """UppercaseStr SHALL convert to uppercase.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.4**
        """
        class TestModel(BaseModel):
            code: UppercaseStr
        
        model = TestModel(code="hello")
        assert model.code == "HELLO"


class TestOptimizedBaseModel:
    """Tests for OptimizedBaseModel.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 3.4**
    """

    def test_to_json_bytes(self) -> None:
        """to_json_bytes SHALL serialize to bytes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.3**
        """
        class TestModel(OptimizedBaseModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        json_bytes = model.to_json_bytes()
        
        assert isinstance(json_bytes, bytes)
        data = json.loads(json_bytes)
        assert data["name"] == "test"
        assert data["value"] == 42

    def test_from_json_bytes(self) -> None:
        """from_json_bytes SHALL parse from bytes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 3.2**
        """
        class TestModel(OptimizedBaseModel):
            name: str
            value: int
        
        json_bytes = b'{"name": "test", "value": 42}'
        model = TestModel.from_json_bytes(json_bytes)
        
        assert model.name == "test"
        assert model.value == 42
