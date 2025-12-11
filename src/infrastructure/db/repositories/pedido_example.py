"""Repository for PedidoExample persistence.

Demonstrates:
- Aggregate root persistence
- Child entity handling
- Eager loading relationships
- Multi-tenant filtering

**Feature: example-system-demo**
**Refactored: Extracted from examples.py for one-class-per-file compliance**
"""

import structlog
from sqlalchemy import and_, false, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.examples.item.entity import Money
from domain.examples.pedido.entity import (
    PedidoExample,
    PedidoItemExample,
    PedidoStatus,
)
from infrastructure.db.models.examples import (
    PedidoExampleModel,
    PedidoItemExampleModel,
)

logger = structlog.get_logger(__name__)


class PedidoExampleRepository:
    """Repository for PedidoExample persistence.

    Demonstrates:
    - Aggregate root persistence
    - Child entity handling
    - Eager loading relationships
    - Multi-tenant filtering
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: PedidoExampleModel) -> PedidoExample:
        """Map database model to domain entity."""
        entity = PedidoExample(
            id=model.id,
            customer_id=model.customer_id,
            customer_name=model.customer_name,
            customer_email=model.customer_email,
            status=PedidoStatus(model.status),
            shipping_address=model.shipping_address,
            notes=model.notes,
            tenant_id=model.tenant_id,
            metadata=model.extra_data or {},
            created_by=model.created_by,
            updated_by=model.updated_by,
        )
        entity.created_at = model.created_at
        entity.updated_at = model.updated_at
        entity.is_deleted = model.is_deleted
        entity.deleted_at = model.deleted_at

        # Map items
        entity.items = [
            PedidoItemExample(
                id=item.id,
                pedido_id=item.pedido_id,
                item_id=item.item_id,
                item_name=item.item_name,
                quantity=item.quantity,
                unit_price=Money(item.unit_price_amount, item.unit_price_currency),
                discount=item.discount,
            )
            for item in model.items
        ]

        return entity

    def _to_model(self, entity: PedidoExample) -> PedidoExampleModel:
        """Map domain entity to database model."""
        model = PedidoExampleModel(
            id=entity.id,
            customer_id=entity.customer_id,
            customer_name=entity.customer_name,
            customer_email=entity.customer_email,
            status=entity.status.value,
            shipping_address=entity.shipping_address,
            notes=entity.notes,
            tenant_id=entity.tenant_id,
            extra_data=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
            deleted_at=entity.deleted_at,
        )

        model.items = [
            PedidoItemExampleModel(
                id=item.id,
                pedido_id=item.pedido_id,
                item_id=item.item_id,
                item_name=item.item_name,
                quantity=item.quantity,
                unit_price_amount=item.unit_price.amount,
                unit_price_currency=item.unit_price.currency,
                discount=item.discount,
            )
            for item in entity.items
        ]

        return model

    async def get(self, pedido_id: str) -> PedidoExample | None:
        """Get order by ID with items."""
        stmt = (
            select(PedidoExampleModel)
            .where(
                and_(
                    PedidoExampleModel.id == pedido_id,
                    PedidoExampleModel.is_deleted.is_(false()),
                )
            )
            .options(selectinload(PedidoExampleModel.items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, entity: PedidoExample) -> PedidoExample:
        """Create a new order with items."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model, ["items"])
        logger.debug("Created PedidoExample", pedido_id=model.id)
        return self._to_entity(model)

    async def update(self, entity: PedidoExample) -> PedidoExample:
        """Update an order."""
        stmt = (
            select(PedidoExampleModel)
            .where(PedidoExampleModel.id == entity.id)
            .options(selectinload(PedidoExampleModel.items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.customer_name = entity.customer_name
            model.customer_email = entity.customer_email
            model.status = entity.status.value
            model.shipping_address = entity.shipping_address
            model.notes = entity.notes
            model.extra_data = entity.metadata
            model.updated_at = entity.updated_at
            model.updated_by = entity.updated_by
            model.is_deleted = entity.is_deleted
            model.deleted_at = entity.deleted_at

            # Sync items - remove old, add new
            model.items.clear()
            for item in entity.items:
                model.items.append(
                    PedidoItemExampleModel(
                        id=item.id,
                        pedido_id=item.pedido_id,
                        item_id=item.item_id,
                        item_name=item.item_name,
                        quantity=item.quantity,
                        unit_price_amount=item.unit_price.amount,
                        unit_price_currency=item.unit_price.currency,
                        discount=item.discount,
                    )
                )

            await self._session.commit()
            await self._session.refresh(model, ["items"])
            logger.debug("Updated PedidoExample", pedido_id=model.id)
            return self._to_entity(model)

        raise ValueError(f"PedidoExample {entity.id} not found")

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        customer_id: str | None = None,
        status: str | None = None,
        tenant_id: str | None = None,
    ) -> list[PedidoExample]:
        """Get all orders with pagination and filtering."""
        conditions = [PedidoExampleModel.is_deleted.is_(false())]

        if customer_id:
            conditions.append(PedidoExampleModel.customer_id == customer_id)
        if status:
            conditions.append(PedidoExampleModel.status == status)
        if tenant_id:
            conditions.append(PedidoExampleModel.tenant_id == tenant_id)

        stmt = (
            select(PedidoExampleModel)
            .where(and_(*conditions))
            .options(selectinload(PedidoExampleModel.items))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(PedidoExampleModel.created_at.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
