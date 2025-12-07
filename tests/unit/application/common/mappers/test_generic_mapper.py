"""Tests for generic mapper module."""

import pytest
from pydantic import BaseModel

from application.common.mappers.errors.mapper_error import MapperError
from application.common.mappers.implementations.generic_mapper import GenericMapper


class SourceEntity(BaseModel):
    """Source entity for testing."""

    id: int
    name: str
    email: str
    internal_field: str = "internal"


class TargetDTO(BaseModel):
    """Target DTO for testing."""

    id: int
    name: str
    email: str


class RenamedTargetDTO(BaseModel):
    """Target DTO with renamed fields."""

    identifier: int
    full_name: str
    email_address: str


class RequiredFieldDTO(BaseModel):
    """DTO with required field not in source."""

    id: int
    name: str
    required_field: str


class TestGenericMapper:
    """Tests for GenericMapper class."""

    def test_init_default(self) -> None:
        mapper = GenericMapper(SourceEntity, TargetDTO)
        assert mapper._source_type == SourceEntity
        assert mapper._target_type == TargetDTO
        assert mapper._field_mapping == {}
        assert mapper._exclude_fields == set()

    def test_init_with_field_mapping(self) -> None:
        mapping = {"id": "identifier"}
        mapper = GenericMapper(SourceEntity, RenamedTargetDTO, field_mapping=mapping)
        assert mapper._field_mapping == mapping

    def test_init_with_exclude_fields(self) -> None:
        exclude = {"internal_field"}
        mapper = GenericMapper(SourceEntity, TargetDTO, exclude_fields=exclude)
        assert mapper._exclude_fields == exclude

    def test_to_dto_maps_matching_fields(self) -> None:
        mapper = GenericMapper(SourceEntity, TargetDTO)
        entity = SourceEntity(id=1, name="Test", email="test@example.com")
        result = mapper.to_dto(entity)
        assert result.id == 1
        assert result.name == "Test"
        assert result.email == "test@example.com"

    def test_to_dto_with_field_mapping(self) -> None:
        mapping = {"id": "identifier", "name": "full_name", "email": "email_address"}
        mapper = GenericMapper(SourceEntity, RenamedTargetDTO, field_mapping=mapping)
        entity = SourceEntity(id=1, name="Test", email="test@example.com")
        result = mapper.to_dto(entity)
        assert result.identifier == 1
        assert result.full_name == "Test"
        assert result.email_address == "test@example.com"

    def test_to_dto_excludes_fields(self) -> None:
        mapper = GenericMapper(SourceEntity, TargetDTO, exclude_fields={"internal_field"})
        entity = SourceEntity(id=1, name="Test", email="test@example.com")
        result = mapper.to_dto(entity)
        assert result.id == 1
        assert not hasattr(result, "internal_field")

    def test_to_entity_maps_matching_fields(self) -> None:
        mapper = GenericMapper(SourceEntity, TargetDTO)
        dto = TargetDTO(id=1, name="Test", email="test@example.com")
        result = mapper.to_entity(dto)
        assert result.id == 1
        assert result.name == "Test"
        assert result.email == "test@example.com"

    def test_to_entity_with_field_mapping(self) -> None:
        mapping = {"id": "identifier", "name": "full_name", "email": "email_address"}
        mapper = GenericMapper(SourceEntity, RenamedTargetDTO, field_mapping=mapping)
        dto = RenamedTargetDTO(identifier=1, full_name="Test", email_address="test@example.com")
        result = mapper.to_entity(dto)
        assert result.id == 1
        assert result.name == "Test"
        assert result.email == "test@example.com"

    def test_to_dto_raises_on_missing_required_field(self) -> None:
        mapper = GenericMapper(SourceEntity, RequiredFieldDTO)
        entity = SourceEntity(id=1, name="Test", email="test@example.com")
        with pytest.raises(MapperError) as exc_info:
            mapper.to_dto(entity)
        assert "required_field" in str(exc_info.value)

    def test_round_trip_preserves_data(self) -> None:
        mapper = GenericMapper(SourceEntity, TargetDTO)
        entity = SourceEntity(id=1, name="Test", email="test@example.com")
        dto = mapper.to_dto(entity)
        result = mapper.to_entity(dto)
        assert result.id == entity.id
        assert result.name == entity.name
        assert result.email == entity.email


class NestedEntity(BaseModel):
    """Entity with nested BaseModel."""

    id: int
    nested: SourceEntity


class NestedDTO(BaseModel):
    """DTO with nested dict."""

    id: int
    nested: dict


class TestGenericMapperNestedObjects:
    """Tests for GenericMapper with nested objects."""

    def test_maps_nested_basemodel_to_dict(self) -> None:
        mapper = GenericMapper(NestedEntity, NestedDTO)
        nested = SourceEntity(id=2, name="Nested", email="nested@example.com")
        entity = NestedEntity(id=1, nested=nested)
        result = mapper.to_dto(entity)
        assert result.id == 1
        assert isinstance(result.nested, dict)
        assert result.nested["id"] == 2
        assert result.nested["name"] == "Nested"


class ListEntity(BaseModel):
    """Entity with list."""

    id: int
    items: list[str]


class ListDTO(BaseModel):
    """DTO with list."""

    id: int
    items: list[str]


class TestGenericMapperLists:
    """Tests for GenericMapper with lists."""

    def test_maps_list(self) -> None:
        mapper = GenericMapper(ListEntity, ListDTO)
        entity = ListEntity(id=1, items=["a", "b", "c"])
        result = mapper.to_dto(entity)
        assert result.items == ["a", "b", "c"]

    def test_maps_empty_list(self) -> None:
        mapper = GenericMapper(ListEntity, ListDTO)
        entity = ListEntity(id=1, items=[])
        result = mapper.to_dto(entity)
        assert result.items == []


class DictEntity(BaseModel):
    """Entity with dict."""

    id: int
    data: dict[str, int]


class DictDTO(BaseModel):
    """DTO with dict."""

    id: int
    data: dict[str, int]


class TestGenericMapperDicts:
    """Tests for GenericMapper with dicts."""

    def test_maps_dict(self) -> None:
        mapper = GenericMapper(DictEntity, DictDTO)
        entity = DictEntity(id=1, data={"a": 1, "b": 2})
        result = mapper.to_dto(entity)
        assert result.data == {"a": 1, "b": 2}


class NullableEntity(BaseModel):
    """Entity with nullable field."""

    id: int
    optional: str | None = None


class NullableDTO(BaseModel):
    """DTO with nullable field."""

    id: int
    optional: str | None = None


class TestGenericMapperNullable:
    """Tests for GenericMapper with nullable fields."""

    def test_maps_none_value(self) -> None:
        mapper = GenericMapper(NullableEntity, NullableDTO)
        entity = NullableEntity(id=1, optional=None)
        result = mapper.to_dto(entity)
        assert result.optional is None

    def test_maps_non_none_value(self) -> None:
        mapper = GenericMapper(NullableEntity, NullableDTO)
        entity = NullableEntity(id=1, optional="value")
        result = mapper.to_dto(entity)
        assert result.optional == "value"
