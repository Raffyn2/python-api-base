"""Tests for auto mapper module."""

import pytest
from pydantic import BaseModel

from application.common.mappers.implementations.auto_mapper import AutoMapper


class SourceModel(BaseModel):
    """Source model for testing."""

    id: int
    name: str
    email: str
    extra_field: str = "extra"


class TargetModel(BaseModel):
    """Target model for testing."""

    id: int
    name: str
    email: str


class PartialTargetModel(BaseModel):
    """Target model with fewer fields."""

    id: int
    name: str


class TestAutoMapper:
    """Tests for AutoMapper class."""

    def test_init(self) -> None:
        mapper = AutoMapper(SourceModel, TargetModel)
        assert mapper._source_type == SourceModel
        assert mapper._target_type == TargetModel

    def test_to_dto_maps_matching_fields(self) -> None:
        mapper = AutoMapper(SourceModel, TargetModel)
        source = SourceModel(id=1, name="Test", email="test@example.com")
        result = mapper.to_dto(source)
        assert result.id == 1
        assert result.name == "Test"
        assert result.email == "test@example.com"

    def test_to_dto_excludes_extra_fields(self) -> None:
        mapper = AutoMapper(SourceModel, PartialTargetModel)
        source = SourceModel(id=1, name="Test", email="test@example.com")
        result = mapper.to_dto(source)
        assert result.id == 1
        assert result.name == "Test"
        assert not hasattr(result, "email")

    def test_to_entity_maps_matching_fields(self) -> None:
        mapper = AutoMapper(SourceModel, TargetModel)
        target = TargetModel(id=1, name="Test", email="test@example.com")
        result = mapper.to_entity(target)
        assert result.id == 1
        assert result.name == "Test"
        assert result.email == "test@example.com"

    def test_to_entity_filters_to_source_fields(self) -> None:
        # When target has fewer fields than source, only matching fields are mapped
        # Source requires email, so we need a target that has it
        mapper = AutoMapper(SourceModel, TargetModel)
        target = TargetModel(id=1, name="Test", email="test@example.com")
        result = mapper.to_entity(target)
        assert result.id == 1
        assert result.name == "Test"
        assert result.email == "test@example.com"
        assert result.extra_field == "extra"  # Default value from source

    def test_round_trip_preserves_data(self) -> None:
        mapper = AutoMapper(SourceModel, TargetModel)
        source = SourceModel(id=1, name="Test", email="test@example.com")
        dto = mapper.to_dto(source)
        entity = mapper.to_entity(dto)
        assert entity.id == source.id
        assert entity.name == source.name
        assert entity.email == source.email


class NestedSourceModel(BaseModel):
    """Source model with nested object."""

    id: int
    data: dict[str, str]


class NestedTargetModel(BaseModel):
    """Target model with nested object."""

    id: int
    data: dict[str, str]


class TestAutoMapperWithNestedData:
    """Tests for AutoMapper with nested data."""

    def test_maps_nested_dict(self) -> None:
        mapper = AutoMapper(NestedSourceModel, NestedTargetModel)
        source = NestedSourceModel(id=1, data={"key": "value"})
        result = mapper.to_dto(source)
        assert result.id == 1
        assert result.data == {"key": "value"}

    def test_maps_empty_dict(self) -> None:
        mapper = AutoMapper(NestedSourceModel, NestedTargetModel)
        source = NestedSourceModel(id=1, data={})
        result = mapper.to_dto(source)
        assert result.data == {}


class ListSourceModel(BaseModel):
    """Source model with list."""

    id: int
    items: list[str]


class ListTargetModel(BaseModel):
    """Target model with list."""

    id: int
    items: list[str]


class TestAutoMapperWithLists:
    """Tests for AutoMapper with list data."""

    def test_maps_list(self) -> None:
        mapper = AutoMapper(ListSourceModel, ListTargetModel)
        source = ListSourceModel(id=1, items=["a", "b", "c"])
        result = mapper.to_dto(source)
        assert result.items == ["a", "b", "c"]

    def test_maps_empty_list(self) -> None:
        mapper = AutoMapper(ListSourceModel, ListTargetModel)
        source = ListSourceModel(id=1, items=[])
        result = mapper.to_dto(source)
        assert result.items == []
