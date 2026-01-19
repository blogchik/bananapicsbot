"""Payment repository implementation."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.payment import Payment, PaymentProvider, PaymentStatus
from app.domain.interfaces.repositories import IPaymentRepository
from app.infrastructure.database.models import PaymentModel
from app.infrastructure.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[PaymentModel], IPaymentRepository):
    """Payment repository implementation."""

    model = PaymentModel

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _to_entity(self, model: PaymentModel) -> Payment:
        """Convert ORM model to domain entity."""
        return Payment(
            id=model.id,
            telegram_id=model.telegram_id,
            provider=PaymentProvider(model.provider),
            provider_payment_id=model.provider_payment_id,
            amount=model.amount,
            credits=model.credits,
            currency=model.currency,
            status=PaymentStatus(model.status),
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    async def create(
        self,
        telegram_id: int,
        provider: PaymentProvider,
        amount: Decimal,
        credits: Decimal,
        currency: str = "XTR",
    ) -> Payment:
        """Create payment record."""
        model = PaymentModel(
            telegram_id=telegram_id,
            provider=provider.value,
            amount=amount,
            credits=credits,
            currency=currency,
            status=PaymentStatus.PENDING.value,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID."""
        query = select(PaymentModel).where(PaymentModel.id == payment_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_provider_id(
        self,
        provider: PaymentProvider,
        provider_payment_id: str,
    ) -> Optional[Payment]:
        """Get payment by provider's payment ID."""
        query = select(PaymentModel).where(
            and_(
                PaymentModel.provider == provider.value,
                PaymentModel.provider_payment_id == provider_payment_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        provider_payment_id: Optional[str] = None,
    ) -> bool:
        """Update payment status."""
        values: Dict[str, Any] = {"status": status.value}

        if provider_payment_id:
            values["provider_payment_id"] = provider_payment_id

        if status == PaymentStatus.COMPLETED:
            values["completed_at"] = datetime.utcnow()

        query = (
            update(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .values(**values)
        )
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def get_user_payments(
        self,
        telegram_id: int,
        status: Optional[PaymentStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Payment]:
        """Get user's payments."""
        query = select(PaymentModel).where(PaymentModel.telegram_id == telegram_id)

        if status:
            query = query.where(PaymentModel.status == status.value)

        query = (
            query.order_by(PaymentModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_stats(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get payment statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total payments
        total_query = select(func.count()).select_from(PaymentModel).where(
            PaymentModel.created_at >= since
        )
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0

        # Completed payments
        completed_query = select(func.count()).select_from(PaymentModel).where(
            and_(
                PaymentModel.created_at >= since,
                PaymentModel.status == PaymentStatus.COMPLETED.value,
            )
        )
        completed_result = await self.session.execute(completed_query)
        completed = completed_result.scalar() or 0

        # Total amount
        amount_query = select(
            func.coalesce(func.sum(PaymentModel.amount), Decimal("0"))
        ).where(
            and_(
                PaymentModel.created_at >= since,
                PaymentModel.status == PaymentStatus.COMPLETED.value,
            )
        )
        amount_result = await self.session.execute(amount_query)
        total_amount = amount_result.scalar() or Decimal("0")

        # Total credits
        credits_query = select(
            func.coalesce(func.sum(PaymentModel.credits), Decimal("0"))
        ).where(
            and_(
                PaymentModel.created_at >= since,
                PaymentModel.status == PaymentStatus.COMPLETED.value,
            )
        )
        credits_result = await self.session.execute(credits_query)
        total_credits = credits_result.scalar() or Decimal("0")

        # By provider
        by_provider_query = (
            select(
                PaymentModel.provider,
                func.count().label("count"),
                func.sum(PaymentModel.amount).label("amount"),
            )
            .where(
                and_(
                    PaymentModel.created_at >= since,
                    PaymentModel.status == PaymentStatus.COMPLETED.value,
                )
            )
            .group_by(PaymentModel.provider)
        )
        by_provider_result = await self.session.execute(by_provider_query)
        by_provider = {
            row.provider: {"count": row.count, "amount": float(row.amount or 0)}
            for row in by_provider_result.all()
        }

        return {
            "period_days": days,
            "total_payments": total,
            "completed_payments": completed,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "total_amount": float(total_amount),
            "total_credits": float(total_credits),
            "by_provider": by_provider,
        }

    async def get_daily_stats(
        self,
        days: int = 7,
    ) -> Sequence[Dict[str, Any]]:
        """Get daily payment statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(PaymentModel.created_at).label("date"),
                func.count().label("count"),
                func.sum(PaymentModel.amount).label("amount"),
            )
            .where(
                and_(
                    PaymentModel.created_at >= since,
                    PaymentModel.status == PaymentStatus.COMPLETED.value,
                )
            )
            .group_by(func.date(PaymentModel.created_at))
            .order_by(func.date(PaymentModel.created_at))
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "count": row.count,
                "amount": float(row.amount or 0),
            }
            for row in result.all()
        ]
