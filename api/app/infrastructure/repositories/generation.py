"""Generation repository implementation."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.generation import (
    Generation,
    GenerationCreate,
    GenerationStatus,
)
from app.domain.interfaces.repositories import IGenerationRepository
from app.infrastructure.database.models import (
    GenerationModel,
    GenerationResultModel,
    ModelCatalogModel,
)
from app.infrastructure.repositories.base import BaseRepository


class GenerationRepository(BaseRepository[GenerationModel], IGenerationRepository):
    """Generation repository implementation."""

    model = GenerationModel

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _to_entity(self, model: GenerationModel) -> Generation:
        """Convert ORM model to domain entity."""
        return Generation(
            id=model.id,
            public_id=model.public_id,
            telegram_id=model.telegram_id,
            model_id=model.model_id,
            prompt=model.prompt,
            negative_prompt=model.negative_prompt,
            input_image_url=model.input_image_url,
            input_params=model.input_params,
            width=model.width,
            height=model.height,
            status=GenerationStatus(model.status),
            credits_charged=model.credits_charged,
            created_at=model.created_at,
            completed_at=model.completed_at,
            result_urls=None,  # Load separately if needed
        )

    async def get_by_id(self, generation_id: UUID) -> Optional[Generation]:
        """Get generation by ID."""
        query = select(GenerationModel).where(GenerationModel.id == generation_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_public_id(self, public_id: str) -> Optional[Generation]:
        """Get generation by public ID."""
        query = select(GenerationModel).where(GenerationModel.public_id == public_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, generation_data: GenerationCreate) -> Generation:
        """Create new generation."""
        model = GenerationModel(
            telegram_id=generation_data.telegram_id,
            model_id=generation_data.model_id,
            prompt=generation_data.prompt,
            negative_prompt=generation_data.negative_prompt,
            input_image_url=generation_data.input_image_url,
            input_params=generation_data.input_params,
            width=generation_data.width,
            height=generation_data.height,
            credits_charged=generation_data.credits_charged,
            status=GenerationStatus.PENDING.value,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update_status(
        self,
        generation_id: UUID,
        status: GenerationStatus,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update generation status."""
        values: Dict[str, Any] = {"status": status.value}

        if status in (GenerationStatus.COMPLETED, GenerationStatus.FAILED):
            values["completed_at"] = datetime.utcnow()

        query = update(GenerationModel).where(GenerationModel.id == generation_id).values(**values)
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def get_user_generations(
        self,
        telegram_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Generation]:
        """Get user's generations."""
        query = (
            select(GenerationModel)
            .where(GenerationModel.telegram_id == telegram_id)
            .order_by(GenerationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_pending_generations(self, limit: int = 100) -> Sequence[Generation]:
        """Get pending generations for processing."""
        query = (
            select(GenerationModel)
            .where(GenerationModel.status == GenerationStatus.PENDING.value)
            .order_by(GenerationModel.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_user_generations(
        self,
        telegram_id: int,
        status: Optional[GenerationStatus] = None,
    ) -> int:
        """Count user's generations."""
        query = select(func.count()).select_from(GenerationModel).where(GenerationModel.telegram_id == telegram_id)

        if status:
            query = query.where(GenerationModel.status == status.value)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_result_urls(self, generation_id: UUID) -> Sequence[str]:
        """Get generation result URLs."""
        query = select(GenerationResultModel.image_url).where(GenerationResultModel.generation_id == generation_id)
        result = await self.session.execute(query)
        return [r for r in result.scalars().all()]

    async def add_result(
        self,
        generation_id: UUID,
        image_url: str,
        index: int = 0,
    ) -> None:
        """Add generation result."""
        model = GenerationResultModel(
            generation_id=generation_id,
            image_url=image_url,
            index=index,
        )
        self.session.add(model)
        await self.session.flush()

    async def get_stats(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get generation statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total generations
        total_query = select(func.count()).select_from(GenerationModel).where(GenerationModel.created_at >= since)
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0

        # Completed
        completed_query = (
            select(func.count())
            .select_from(GenerationModel)
            .where(
                and_(
                    GenerationModel.created_at >= since,
                    GenerationModel.status == GenerationStatus.COMPLETED.value,
                )
            )
        )
        completed_result = await self.session.execute(completed_query)
        completed = completed_result.scalar() or 0

        # Failed
        failed_query = (
            select(func.count())
            .select_from(GenerationModel)
            .where(
                and_(
                    GenerationModel.created_at >= since,
                    GenerationModel.status == GenerationStatus.FAILED.value,
                )
            )
        )
        failed_result = await self.session.execute(failed_query)
        failed = failed_result.scalar() or 0

        # Credits used
        credits_query = select(func.coalesce(func.sum(GenerationModel.credits_charged), Decimal("0"))).where(
            and_(
                GenerationModel.created_at >= since,
                GenerationModel.status == GenerationStatus.COMPLETED.value,
            )
        )
        credits_result = await self.session.execute(credits_query)
        credits_used = credits_result.scalar() or Decimal("0")

        # By model
        by_model_query = (
            select(
                ModelCatalogModel.slug,
                func.count(GenerationModel.id).label("count"),
            )
            .join(ModelCatalogModel, GenerationModel.model_id == ModelCatalogModel.id)
            .where(GenerationModel.created_at >= since)
            .group_by(ModelCatalogModel.slug)
        )
        by_model_result = await self.session.execute(by_model_query)
        by_model = {row.slug: row.count for row in by_model_result.all()}

        return {
            "period_days": days,
            "total_generations": total,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "credits_used": float(credits_used),
            "by_model": by_model,
        }

    async def get_daily_stats(
        self,
        days: int = 7,
    ) -> Sequence[Dict[str, Any]]:
        """Get daily generation statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(GenerationModel.created_at).label("date"),
                func.count(GenerationModel.id).label("count"),
                func.sum(
                    func.case(
                        (GenerationModel.status == GenerationStatus.COMPLETED.value, 1),
                        else_=0,
                    )
                ).label("completed"),
            )
            .where(GenerationModel.created_at >= since)
            .group_by(func.date(GenerationModel.created_at))
            .order_by(func.date(GenerationModel.created_at))
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "count": row.count,
                "completed": row.completed or 0,
            }
            for row in result.all()
        ]
