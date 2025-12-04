"""Repository for ItemExample persistence.

Demonstrates:
- Async SQLAlchemy operations
- Entity to model mapping
- Soft delete filtering
- Query builder usage

**Feature: example-system-demo**
**Refactored: Extracted from examples.py for one-class-per-file compliance**
"""

import logging

from sqlalchemy import and_, false, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.examples.item.entity import ItemExample, ItemExampleStatus, Money
from infrastructure.db.models.examples import ItemExampleModel

logger = logging.getLogger(__name__)


class ItemExampleRepository:
    """Repository for ItemExample persistence.

    Demonstrates:
    - Async SQLAlchemy operations
    - Entity to model mapping
    - Soft delete filtering
    - Query builder usage
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: ItemExampleModel) -> ItemExample:
        """Map database model to domain entity."""
        entity = ItemExample(
            id=model.id,
            name=model.name,
            description=model.description,
            sku=model.sku,
            price=Money(model.price_amount, model.price_currency),
            quantity=model.quantity,
            status=ItemExampleStatus(model.status),
            category=model.category,
            tags=model.tags or [],
            metadata=model.extra_data or {},
            created_by=model.created_by,
            updated_by=model.updated_by,
        )
        entity.created_at = model.created_at
        entity.updated_at = model.updated_at
        entity.is_deleted = model.is_deleted
        entity.deleted_at = model.deleted_at
        return entity

    def _to_model(self, entity: ItemExample) -> ItemExampleModel:
        """Map domain entity to database model."""
        return ItemExampleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            sku=entity.sku,
            price_amount=entity.price.amount,
            price_currency=entity.price.currency,
            quantity=entity.quantity,
            status=entity.status.value,
            category=entity.category,
            tags=entity.tags,
            extra_data=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
            deleted_at=entity.deleted_at,
        )

    async def get(self, item_id: str) -> ItemExample | None:
        """Get item by ID."""
        stmt = select(ItemExampleModel).where(
            and_(
                ItemExampleModel.id == item_id,
                ItemExampleModel.is_deleted.is_(false()),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_sku(self, sku: str) -> ItemExample | None:
        """Get item by SKU."""
        stmt = select(ItemExampleModel).where(
            and_(
                ItemExampleModel.sku == sku,
                ItemExampleModel.is_deleted.is_(false()),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, entity: ItemExample) -> ItemExample:
        """Create a new item."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        logger.debug("Created ItemExample: %s", model.id)
        return self._to_entity(model)

    async def update(self, entity: ItemExample) -> ItemExample:
        """Update an existing item."""
        stmt = select(ItemExampleModel).where(ItemExampleModel.id == entity.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = entity.name
            model.description = entity.description
            model.sku = entity.sku
            model.price_amount = entity.price.amount
            model.price_currency = entity.price.currency
            model.quantity = entity.quantity
            model.status = entity.status.value
            model.category = entity.category
            model.tags = entity.tags
            model.extra_data = entity.metadata
            model.updated_at = entity.updated_at
            model.updated_by = entity.updated_by
            model.is_deleted = entity.is_deleted
            model.deleted_at = entity.deleted_at

            await self._session.commit()
            await self._session.refresh(model)
            logger.debug("Updated ItemExample: %s", model.id)
            return self._to_entity(model)

        raise ValueError(f"ItemExample {entity.id} not found")

    async def delete(self, item_id: str) -> bool:
        """Hard delete an item (use soft delete via update instead)."""
        stmt = select(ItemExampleModel).where(ItemExampleModel.id == item_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        status: str | None = None,
    ) -> list[ItemExample]:
        """Get all items with pagination and filtering."""
        conditions = [ItemExampleModel.is_deleted.is_(false())]

        if category:
            conditions.append(ItemExampleModel.category == category)
        if status:
            conditions.append(ItemExampleModel.status == status)

        stmt = (
            select(ItemExampleModel)
            .where(and_(*conditions))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(ItemExampleModel.created_at.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
