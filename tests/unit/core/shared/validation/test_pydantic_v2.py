"""Tests for Pydantic V2 validation utilities.

**Feature: realistic-test-coverage**
**Validates: Requirements 3.1, 3.2, 3.3**
"""

import json

import pytest
from pydantic import BaseModel, ValidationError

from core.shared.validation.pydantic_v2 import (
    ComputedFieldExample,
    EmailStr,
    LowercaseStr,
    OptimizedBaseModel,
    StrippedStr,
    TypeAdapterCache,
    UppercaseStr,
    get_type_adapter,
    lowercase,
    strip_whitespace,
    uppercase,
    validate_bulk,
    validate_bulk_json,
    validate_json_fast,
)


class SampleModel(BaseModel):
    """Sample model for testing."""

    name: str
    age: int


class TestTypeAdapterCache:
    """Tests for TypeAdapterCache."""

    def test_validate_json_bytes(self) -> None:
        """Test validating JSON bytes."""
        cache = TypeAdapterCache(SampleModel)
        result = cache.validate_json(b'{"name": "John", "age": 30}')
        assert result.name == "John"
        assert result.age == 30

    def test_validate_json_string(self) -> None:
        """Test validating JSON string."""
        cache = TypeAdapterCache(SampleModel)
        result = cache.validate_json('{"name": "Jane", "age": 25}')
        assert result.name == "Jane"
        assert result.age == 25

    def test_validate_list_json(self) -> None:
        """Test validating JSON array."""
        cache = TypeAdapterCache(SampleModel)
        result = cache.validate_list_json(
            b'[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]'
        )
        assert len(result) == 2
        assert result[0].name == "John"
        assert result[1].name == "Jane"

    def test_validate_python(self) -> None:
        """Test validating Python dict."""
        cache = TypeAdapterCache(SampleModel)
        result = cache.validate_python({"name": "Bob", "age": 40})
        assert result.name == "Bob"
        assert result.age == 40

    def test_dump_json(self) -> None:
        """Test serializing to JSON bytes."""
        cache = TypeAdapterCache(SampleModel)
        model = SampleModel(name="Test", age=20)
        result = cache.dump_json(model)
        assert isinstance(result, bytes)
        data = json.loads(result)
        assert data["name"] == "Test"
        assert data["age"] == 20

    def test_dump_json_list(self) -> None:
        """Test serializing list to JSON bytes."""
        cache = TypeAdapterCache(SampleModel)
        models = [
            SampleModel(name="A", age=1),
            SampleModel(name="B", age=2),
        ]
        result = cache.dump_json_list(models)
        assert isinstance(result, bytes)
        data = json.loads(result)
        assert len(data) == 2

    def test_adapter_caching(self) -> None:
        """Test that adapter is cached."""
        cache = TypeAdapterCache(SampleModel)
        adapter1 = cache.adapter
        adapter2 = cache.adapter
        assert adapter1 is adapter2

    def test_list_adapter_caching(self) -> None:
        """Test that list adapter is cached."""
        cache = TypeAdapterCache(SampleModel)
        adapter1 = cache.list_adapter
        adapter2 = cache.list_adapter
        assert adapter1 is adapter2


class TestGetTypeAdapter:
    """Tests for get_type_adapter function."""

    def test_returns_type_adapter(self) -> None:
        """Test that function returns TypeAdapter."""
        adapter = get_type_adapter(SampleModel)
        assert adapter is not None

    def test_caches_adapter(self) -> None:
        """Test that adapter is cached."""
        adapter1 = get_type_adapter(SampleModel)
        adapter2 = get_type_adapter(SampleModel)
        assert adapter1 is adapter2


class TestValidateJsonFast:
    """Tests for validate_json_fast function."""

    def test_validate_bytes(self) -> None:
        """Test validating JSON bytes."""
        result = validate_json_fast(SampleModel, b'{"name": "Test", "age": 10}')
        assert result.name == "Test"
        assert result.age == 10

    def test_validate_string(self) -> None:
        """Test validating JSON string."""
        result = validate_json_fast(SampleModel, '{"name": "Test", "age": 10}')
        assert result.name == "Test"

    def test_invalid_json_raises_error(self) -> None:
        """Test that invalid JSON raises error."""
        with pytest.raises(ValidationError):
            validate_json_fast(SampleModel, '{"name": 123}')


class TestStringValidators:
    """Tests for string validator functions."""

    def test_strip_whitespace(self) -> None:
        """Test strip_whitespace function."""
        assert strip_whitespace("  hello  ") == "hello"
        assert strip_whitespace("hello") == "hello"

    def test_strip_whitespace_non_string(self) -> None:
        """Test strip_whitespace with non-string."""
        assert strip_whitespace(123) == 123

    def test_lowercase(self) -> None:
        """Test lowercase function."""
        assert lowercase("HELLO") == "hello"
        assert lowercase("Hello World") == "hello world"

    def test_lowercase_non_string(self) -> None:
        """Test lowercase with non-string."""
        assert lowercase(123) == 123

    def test_uppercase(self) -> None:
        """Test uppercase function."""
        assert uppercase("hello") == "HELLO"
        assert uppercase("Hello World") == "HELLO WORLD"

    def test_uppercase_non_string(self) -> None:
        """Test uppercase with non-string."""
        assert uppercase(123) == 123


class TestAnnotatedTypes:
    """Tests for annotated string types."""

    def test_stripped_str(self) -> None:
        """Test StrippedStr type."""

        class Model(BaseModel):
            value: StrippedStr

        result = Model(value="  test  ")
        assert result.value == "test"

    def test_lowercase_str(self) -> None:
        """Test LowercaseStr type."""

        class Model(BaseModel):
            value: LowercaseStr

        result = Model(value="HELLO")
        assert result.value == "hello"

    def test_uppercase_str(self) -> None:
        """Test UppercaseStr type."""

        class Model(BaseModel):
            value: UppercaseStr

        result = Model(value="hello")
        assert result.value == "HELLO"

    def test_email_str(self) -> None:
        """Test EmailStr type (stripped and lowercase)."""

        class Model(BaseModel):
            email: EmailStr

        result = Model(email="  TEST@EXAMPLE.COM  ")
        assert result.email == "test@example.com"


class TestOptimizedBaseModel:
    """Tests for OptimizedBaseModel."""

    def test_to_json_bytes(self) -> None:
        """Test to_json_bytes method."""

        class TestModel(OptimizedBaseModel):
            name: str

        model = TestModel(name="test")
        result = model.to_json_bytes()
        assert isinstance(result, bytes)
        assert b"test" in result

    def test_from_json_bytes(self) -> None:
        """Test from_json_bytes method."""

        class TestModel(OptimizedBaseModel):
            name: str

        result = TestModel.from_json_bytes(b'{"name": "test"}')
        assert result.name == "test"

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are forbidden."""

        class TestModel(OptimizedBaseModel):
            name: str

        with pytest.raises(ValidationError):
            TestModel(name="test", extra="field")


class TestComputedFieldExample:
    """Tests for ComputedFieldExample."""

    def test_full_name_computed(self) -> None:
        """Test full_name computed field."""
        model = ComputedFieldExample(
            first_name="John",
            last_name="Doe",
            price=10.0,
            quantity=5,
        )
        assert model.full_name == "John Doe"

    def test_total_computed(self) -> None:
        """Test total computed field."""
        model = ComputedFieldExample(
            first_name="John",
            last_name="Doe",
            price=10.0,
            quantity=5,
        )
        assert model.total == 50.0

    def test_computed_fields_in_serialization(self) -> None:
        """Test that computed fields are included in serialization."""
        model = ComputedFieldExample(
            first_name="Jane",
            last_name="Smith",
            price=20.0,
            quantity=3,
        )
        data = model.model_dump()
        assert "full_name" in data
        assert "total" in data
        assert data["full_name"] == "Jane Smith"
        assert data["total"] == 60.0


class TestValidateBulk:
    """Tests for validate_bulk function."""

    def test_all_valid(self) -> None:
        """Test bulk validation with all valid items."""
        items = [
            {"name": "A", "age": 1},
            {"name": "B", "age": 2},
            {"name": "C", "age": 3},
        ]
        valid, errors = validate_bulk(SampleModel, items)
        assert len(valid) == 3
        assert len(errors) == 0

    def test_some_invalid(self) -> None:
        """Test bulk validation with some invalid items."""
        items = [
            {"name": "A", "age": 1},
            {"name": "B", "age": "invalid"},  # Invalid
            {"name": "C", "age": 3},
        ]
        valid, errors = validate_bulk(SampleModel, items)
        assert len(valid) == 2
        assert len(errors) == 1
        assert errors[0][0] == 1  # Index of invalid item

    def test_all_invalid(self) -> None:
        """Test bulk validation with all invalid items."""
        items = [
            {"name": 123},  # Invalid
            {"age": "invalid"},  # Invalid
        ]
        valid, errors = validate_bulk(SampleModel, items)
        assert len(valid) == 0
        assert len(errors) == 2

    def test_empty_list(self) -> None:
        """Test bulk validation with empty list."""
        valid, errors = validate_bulk(SampleModel, [])
        assert len(valid) == 0
        assert len(errors) == 0


class TestValidateBulkJson:
    """Tests for validate_bulk_json function."""

    def test_validate_json_array(self) -> None:
        """Test validating JSON array."""
        json_data = b'[{"name": "A", "age": 1}, {"name": "B", "age": 2}]'
        result = validate_bulk_json(SampleModel, json_data)
        assert len(result) == 2
        assert result[0].name == "A"
        assert result[1].name == "B"

    def test_validate_empty_array(self) -> None:
        """Test validating empty JSON array."""
        result = validate_bulk_json(SampleModel, b"[]")
        assert len(result) == 0

    def test_invalid_json_raises_error(self) -> None:
        """Test that invalid JSON raises error."""
        with pytest.raises(ValidationError):
            validate_bulk_json(SampleModel, b'[{"name": 123}]')
