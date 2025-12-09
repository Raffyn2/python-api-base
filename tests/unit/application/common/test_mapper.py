"""Unit tests for generic_mapper.py.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 2.2, 8.3**
"""

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

from application.common.mappers.errors.mapper_error import MapperError
from application.common.mappers.implementations.generic_mapper import GenericMapper


class SourceModel(BaseModel):
    """Source model for mapper tests."""

    id: str
    name: str
    value: int
    optional_field: str | None = None


class TargetModel(BaseModel):
    """Target model for mapper tests."""

    id: str
    name: str
    value: int
    optional_field: str | None = None


class PartialTargetModel(BaseModel):
    """Target model with fewer fields."""

    id: str
    name: str


class RenamedTargetModel(BaseModel):
    """Target model with renamed fields."""

    identifier: str
    title: str
    amount: int


class TestGenericMapper:
    """Tests for GenericMapper class."""

    @pytest.fixture
    def mapper(self) -> GenericMapper[SourceModel, TargetModel]:
        """Create basic mapper."""
        return GenericMapper(SourceModel, TargetModel)

    def test_to_dto_basic(self, mapper: GenericMapper[SourceModel, TargetModel]) -> None:
        """Test basic entity to DTO conversion."""
        source = SourceModel(id="1", name="Test", value=100)
        result = mapper.to_dto(source)

        assert result.id == "1"
        assert result.name == "Test"
        assert result.value == 100

    def test_to_entity_basic(self, mapper: GenericMapper[SourceModel, TargetModel]) -> None:
        """Test basic DTO to entity conversion."""
        target = TargetModel(id="1", name="Test", value=100)
        result = mapper.to_entity(target)

        assert result.id == "1"
        assert result.name == "Test"
        assert result.value == 100

    def test_to_dto_with_optional_field(
        self, mapper: GenericMapper[SourceModel, TargetModel]
    ) -> None:
        """Test conversion with optional field present."""
        source = SourceModel(id="1", name="Test", value=100, optional_field="extra")
        result = mapper.to_dto(source)

        assert result.optional_field == "extra"

    def test_to_dto_with_optional_field_none(
        self, mapper: GenericMapper[SourceModel, TargetModel]
    ) -> None:
        """Test conversion with optional field as None."""
        source = SourceModel(id="1", name="Test", value=100, optional_field=None)
        result = mapper.to_dto(source)

        assert result.optional_field is None

    def test_mapper_with_field_mapping(self) -> None:
        """Test mapper with custom field mapping."""
        mapper = GenericMapper(
            SourceModel,
            RenamedTargetModel,
            field_mapping={"id": "identifier", "name": "title", "value": "amount"},
        )
        source = SourceModel(id="1", name="Test", value=100)
        result = mapper.to_dto(source)

        assert result.identifier == "1"
        assert result.title == "Test"
        assert result.amount == 100

    def test_mapper_with_exclude_fields(self) -> None:
        """Test mapper with excluded fields."""
        mapper = GenericMapper(
            SourceModel,
            PartialTargetModel,
            exclude_fields={"value", "optional_field"},
        )
        source = SourceModel(id="1", name="Test", value=100)
        result = mapper.to_dto(source)

        assert result.id == "1"
        assert result.name == "Test"

    def test_reverse_mapping(self) -> None:
        """Test reverse field mapping for to_entity."""
        mapper = GenericMapper(
            SourceModel,
            RenamedTargetModel,
            field_mapping={"id": "identifier", "name": "title", "value": "amount"},
        )
        target = RenamedTargetModel(identifier="1", title="Test", amount=100)
        result = mapper.to_entity(target)

        assert result.id == "1"
        assert result.name == "Test"
        assert result.value == 100

    def test_map_value_with_none(
        self, mapper: GenericMapper[SourceModel, TargetModel]
    ) -> None:
        """Test _map_value handles None correctly."""
        result = mapper._map_value(None)
        assert result is None

    def test_map_value_with_list(
        self, mapper: GenericMapper[SourceModel, TargetModel]
    ) -> None:
        """Test _map_value handles lists correctly."""
        result = mapper._map_value([1, 2, 3])
        assert result == [1, 2, 3]

    def test_map_value_with_dict(
        self, mapper: GenericMapper[SourceModel, TargetModel]
    ) -> None:
        """Test _map_value handles dicts correctly."""
        result = mapper._map_value({"key": "value"})
        assert result == {"key": "value"}

    def test_map_value_with_nested_model(
        self, mapper: GenericMapper[SourceModel, TargetModel]
    ) -> None:
        """Test _map_value handles nested BaseModel correctly."""
        nested = SourceModel(id="1", name="Nested", value=50)
        result = mapper._map_value(nested)
        assert isinstance(result, dict)
        assert result["id"] == "1"


class TestGenericMapperRoundTrip:
    """Round-trip tests for GenericMapper.

    **Feature: test-coverage-80-percent-v3, Property 1: Mapper Round-trip Consistency**
    **Validates: Requirements 2.2, 8.3**
    """

    @given(
        id=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
        name=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
        value=st.integers(min_value=0, max_value=1000000),
    )
    @settings(max_examples=100, deadline=5000)
    def test_roundtrip_preserves_data(self, id: str, name: str, value: int) -> None:
        """Property test: to_dto then to_entity preserves data.

        **Feature: test-coverage-80-percent-v3, Property 1: Mapper Round-trip Consistency**
        **Validates: Requirements 2.2, 8.3**
        """
        mapper = GenericMapper(SourceModel, TargetModel)
        source = SourceModel(id=id, name=name, value=value)

        dto = mapper.to_dto(source)
        entity = mapper.to_entity(dto)

        assert entity.id == source.id
        assert entity.name == source.name
        assert entity.value == source.value

    @given(
        id=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
        name=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
        value=st.integers(min_value=0, max_value=1000000),
    )
    @settings(max_examples=100, deadline=5000)
    def test_reverse_roundtrip_preserves_data(self, id: str, name: str, value: int) -> None:
        """Property test: to_entity then to_dto preserves data.

        **Feature: test-coverage-80-percent-v3, Property 1: Mapper Round-trip Consistency**
        **Validates: Requirements 2.2, 8.3**
        """
        mapper = GenericMapper(SourceModel, TargetModel)
        target = TargetModel(id=id, name=name, value=value)

        entity = mapper.to_entity(target)
        dto = mapper.to_dto(entity)

        assert dto.id == target.id
        assert dto.name == target.name
        assert dto.value == target.value
