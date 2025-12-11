"""Unit tests for item example mapper.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 8.3**
"""

from datetime import UTC
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

from application.examples.item.dtos import ItemExampleResponse
from application.examples.item.mappers.mapper import ItemExampleMapper
from application.examples.shared.dtos import MoneyDTO
from domain.examples.item.entity import ItemExample, Money


class TestItemExampleMapper:
    """Tests for ItemExampleMapper class."""

    @pytest.fixture()
    def mapper(self) -> ItemExampleMapper:
        """Create mapper instance."""
        return ItemExampleMapper()

    @pytest.fixture()
    def sample_entity(self) -> ItemExample:
        """Create sample entity for testing."""
        return ItemExample.create(
            name="Test Item",
            sku="TEST-001",
            price=Money(Decimal("99.99"), "BRL"),
            description="Test description",
            quantity=10,
            category="electronics",
            tags=["tag1", "tag2"],
            created_by="test_user",
        )

    def test_to_dto_converts_entity(self, mapper: ItemExampleMapper, sample_entity: ItemExample) -> None:
        """Test entity to DTO conversion."""
        dto = mapper.to_dto(sample_entity)

        assert dto.id == sample_entity.id
        assert dto.name == sample_entity.name
        assert dto.sku == sample_entity.sku
        assert dto.description == sample_entity.description
        assert dto.quantity == sample_entity.quantity
        assert dto.category == sample_entity.category
        assert dto.price.amount == sample_entity.price.amount
        assert dto.price.currency == sample_entity.price.currency

    def test_to_entity_converts_dto(self, mapper: ItemExampleMapper) -> None:
        """Test DTO to entity conversion."""
        from datetime import datetime

        now = datetime.now(UTC)
        dto = ItemExampleResponse(
            id="test-id",
            name="Test Item",
            sku="TEST-001",
            price=MoneyDTO(amount=Decimal("99.99"), currency="BRL"),
            description="Test description",
            quantity=10,
            status="active",
            category="electronics",
            tags=["tag1", "tag2"],
            is_available=True,
            total_value=MoneyDTO(amount=Decimal("999.90"), currency="BRL"),
            created_at=now,
            updated_at=now,
            created_by="test_user",
            updated_by="test_user",
        )

        entity = mapper.to_entity(dto)

        assert entity.id == dto.id
        assert entity.name == dto.name
        assert entity.sku == dto.sku
        assert entity.description == dto.description
        assert entity.quantity == dto.quantity
        assert entity.category == dto.category

    def test_to_dto_list_converts_multiple(self, mapper: ItemExampleMapper) -> None:
        """Test batch entity to DTO conversion."""
        entities = [
            ItemExample.create(
                name=f"Item {i}",
                sku=f"SKU-{i:03d}",
                price=Money(Decimal("10.00")),
                description=f"Description {i}",
            )
            for i in range(3)
        ]

        dtos = mapper.to_dto_list(entities)

        assert len(dtos) == 3
        for i, dto in enumerate(dtos):
            assert dto.name == f"Item {i}"
            assert dto.sku == f"SKU-{i:03d}"

    def test_to_entity_list_converts_multiple(self, mapper: ItemExampleMapper) -> None:
        """Test batch DTO to entity conversion."""
        from datetime import datetime

        now = datetime.now(UTC)
        dtos = [
            ItemExampleResponse(
                id=f"id-{i}",
                name=f"Item {i}",
                sku=f"SKU-{i:03d}",
                price=MoneyDTO(amount=Decimal("10.00"), currency="BRL"),
                description=f"Description {i}",
                quantity=i + 1,
                status="active",
                category="test",
                tags=[],
                is_available=True,
                total_value=MoneyDTO(amount=Decimal("10.00"), currency="BRL"),
                created_at=now,
                updated_at=now,
                created_by="test",
                updated_by="test",
            )
            for i in range(3)
        ]

        entities = mapper.to_entity_list(dtos)

        assert len(entities) == 3
        for i, entity in enumerate(entities):
            assert entity.name == f"Item {i}"
            assert entity.sku == f"SKU-{i:03d}"

    def test_static_to_response_method(self, sample_entity: ItemExample) -> None:
        """Test backward compatible static method."""
        dto = ItemExampleMapper.to_response(sample_entity)

        assert dto.id == sample_entity.id
        assert dto.name == sample_entity.name

    def test_static_to_response_list_method(self) -> None:
        """Test backward compatible static list method."""
        entities = [
            ItemExample.create(
                name=f"Item {i}",
                sku=f"SKU-{i:03d}",
                price=Money(Decimal("10.00")),
                description=f"Description {i}",
            )
            for i in range(2)
        ]

        dtos = ItemExampleMapper.to_response_list(entities)

        assert len(dtos) == 2


# Property-based tests


@st.composite
def item_entity_strategy(draw: st.DrawFn) -> ItemExample:
    """Strategy to generate valid ItemExample entities."""
    name = draw(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "S"), whitelist_characters=" -_"),
        ).filter(lambda x: x.strip())
    )

    sku = draw(
        st.text(
            min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip())
    )

    amount = draw(
        st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("999999.99"),
            places=2,
            allow_nan=False,
            allow_infinity=False,
        )
    )

    currency = draw(st.sampled_from(["BRL", "USD", "EUR"]))

    description = draw(st.text(max_size=500).filter(lambda x: "\x00" not in x))

    quantity = draw(st.integers(min_value=0, max_value=10000))

    category = draw(st.sampled_from(["electronics", "clothing", "food", "other"]))

    tags = draw(
        st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))).filter(
                lambda x: x.strip()
            ),
            max_size=5,
        )
    )

    return ItemExample.create(
        name=name,
        sku=sku,
        price=Money(amount, currency),
        description=description,
        quantity=quantity,
        category=category,
        tags=tags,
        created_by="test_user",
    )


class TestItemMapperProperties:
    """Property-based tests for ItemExampleMapper.

    **Feature: test-coverage-80-percent-v3, Property 1: Mapper Round-trip Consistency**
    **Validates: Requirements 2.2, 8.3**
    """

    @given(entity=item_entity_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_mapper_roundtrip_preserves_essential_fields(self, entity: ItemExample) -> None:
        """
        **Feature: test-coverage-80-percent-v3, Property 1: Mapper Round-trip Consistency**
        **Validates: Requirements 2.2, 8.3**

        For any valid domain entity, converting to DTO and back to entity
        should preserve all essential data fields.
        """
        mapper = ItemExampleMapper()

        # Entity -> DTO -> Entity
        dto = mapper.to_dto(entity)
        result = mapper.to_entity(dto)

        # Essential fields should be preserved
        assert result.id == entity.id
        assert result.name == entity.name
        assert result.sku == entity.sku
        assert result.description == entity.description
        assert result.quantity == entity.quantity
        assert result.category == entity.category
        assert result.price.amount == entity.price.amount
        assert result.price.currency == entity.price.currency
        assert result.tags == entity.tags
