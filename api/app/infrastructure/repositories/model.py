"""Model repository implementation."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.model import Model, ModelPrice
from app.domain.interfaces.repositories import IModelRepository
from app.infrastructure.database.models import ModelCatalogModel, ModelPriceModel
from app.infrastructure.repositories.base import BaseRepository


class ModelRepository(BaseRepository[ModelCatalogModel], IModelRepository):
    """Model repository implementation."""

    model = ModelCatalogModel

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _to_entity(
        self,
        model: ModelCatalogModel,
        prices: Optional[Sequence[ModelPriceModel]] = None,
    ) -> Model:
        """Convert ORM model to domain entity."""
        price_entities = []
        if prices:
            price_entities = [
                ModelPrice(
                    id=p.id,
                    model_id=p.model_id,
                    generation_type=p.generation_type,
                    price=p.price,
                    valid_from=p.valid_from,
                    valid_until=p.valid_until,
                )
                for p in prices
            ]

        return Model(
            id=model.id,
            slug=model.slug,
            display_name=model.display_name,
            provider=model.provider,
            model_type=model.model_type,
            supports_t2i=model.supports_t2i,
            supports_i2i=model.supports_i2i,
            sizes=model.sizes,
            is_active=model.is_active,
            created_at=model.created_at,
            prices=price_entities,
        )

    async def get_by_id(self, model_id: int) -> Optional[Model]:
        """Get model by ID."""
        query = select(ModelCatalogModel).where(ModelCatalogModel.id == model_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        prices = await self._get_current_prices(model_id)
        return self._to_entity(model, prices)

    async def get_by_slug(self, slug: str) -> Optional[Model]:
        """Get model by slug."""
        query = select(ModelCatalogModel).where(ModelCatalogModel.slug == slug)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        prices = await self._get_current_prices(model.id)
        return self._to_entity(model, prices)

    async def get_active_models(self) -> Sequence[Model]:
        """Get all active models."""
        query = (
            select(ModelCatalogModel)
            .where(ModelCatalogModel.is_active == True)
            .order_by(ModelCatalogModel.display_name)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        entities = []
        for model in models:
            prices = await self._get_current_prices(model.id)
            entities.append(self._to_entity(model, prices))

        return entities

    async def get_all(self) -> Sequence[Model]:
        """Get all models."""
        query = select(ModelCatalogModel).order_by(ModelCatalogModel.display_name)
        result = await self.session.execute(query)
        models = result.scalars().all()

        entities = []
        for model in models:
            prices = await self._get_current_prices(model.id)
            entities.append(self._to_entity(model, prices))

        return entities

    async def _get_current_prices(self, model_id: int) -> Sequence[ModelPriceModel]:
        """Get current prices for a model."""
        now = datetime.utcnow()
        query = (
            select(ModelPriceModel)
            .where(
                and_(
                    ModelPriceModel.model_id == model_id,
                    ModelPriceModel.valid_from <= now,
                    (ModelPriceModel.valid_until.is_(None)) | (ModelPriceModel.valid_until > now),
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_price(
        self,
        model_id: int,
        generation_type: str,
    ) -> Optional[Decimal]:
        """Get current price for model and generation type."""
        now = datetime.utcnow()
        query = (
            select(ModelPriceModel.price)
            .where(
                and_(
                    ModelPriceModel.model_id == model_id,
                    ModelPriceModel.generation_type == generation_type,
                    ModelPriceModel.valid_from <= now,
                    (ModelPriceModel.valid_until.is_(None)) | (ModelPriceModel.valid_until > now),
                )
            )
            .order_by(ModelPriceModel.valid_from.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def set_active(self, model_id: int, is_active: bool) -> bool:
        """Set model active status."""
        query = (
            update(ModelCatalogModel)
            .where(ModelCatalogModel.id == model_id)
            .values(is_active=is_active)
        )
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def update_price(
        self,
        model_id: int,
        generation_type: str,
        new_price: Decimal,
    ) -> bool:
        """Update model price (creates new price record)."""
        now = datetime.utcnow()

        # End current price
        update_query = (
            update(ModelPriceModel)
            .where(
                and_(
                    ModelPriceModel.model_id == model_id,
                    ModelPriceModel.generation_type == generation_type,
                    ModelPriceModel.valid_until.is_(None),
                )
            )
            .values(valid_until=now)
        )
        await self.session.execute(update_query)

        # Create new price
        new_price_model = ModelPriceModel(
            model_id=model_id,
            generation_type=generation_type,
            price=new_price,
            valid_from=now,
        )
        self.session.add(new_price_model)
        await self.session.flush()

        return True
