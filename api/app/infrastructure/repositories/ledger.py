"""Ledger repository implementation."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.ledger import LedgerEntry, LedgerEntryType
from app.domain.interfaces.repositories import ILedgerRepository
from app.infrastructure.database.models import LedgerEntryModel
from app.infrastructure.repositories.base import BaseRepository


class LedgerRepository(BaseRepository[LedgerEntryModel], ILedgerRepository):
    """Ledger repository implementation."""

    model = LedgerEntryModel

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _to_entity(self, model: LedgerEntryModel) -> LedgerEntry:
        """Convert ORM model to domain entity."""
        return LedgerEntry(
            id=model.id,
            telegram_id=model.telegram_id,
            amount=model.amount,
            entry_type=LedgerEntryType(model.entry_type),
            reason=model.reason,
            reference_id=model.reference_id,
            created_at=model.created_at,
        )

    async def create_entry(
        self,
        telegram_id: int,
        amount: Decimal,
        entry_type: LedgerEntryType,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> LedgerEntry:
        """Create ledger entry."""
        model = LedgerEntryModel(
            telegram_id=telegram_id,
            amount=amount,
            entry_type=entry_type.value,
            reason=reason,
            reference_id=reference_id,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_balance(self, telegram_id: int) -> Decimal:
        """Get user's current balance."""
        query = select(func.coalesce(func.sum(LedgerEntryModel.amount), Decimal("0"))).where(
            LedgerEntryModel.telegram_id == telegram_id
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")

    async def get_user_entries(
        self,
        telegram_id: int,
        entry_type: Optional[LedgerEntryType] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[LedgerEntry]:
        """Get user's ledger entries."""
        query = select(LedgerEntryModel).where(LedgerEntryModel.telegram_id == telegram_id)

        if entry_type:
            query = query.where(LedgerEntryModel.entry_type == entry_type.value)

        query = query.order_by(LedgerEntryModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_total_by_type(
        self,
        entry_type: LedgerEntryType,
        since: Optional[datetime] = None,
    ) -> Decimal:
        """Get total amount by entry type."""
        query = select(func.coalesce(func.sum(LedgerEntryModel.amount), Decimal("0"))).where(
            LedgerEntryModel.entry_type == entry_type.value
        )

        if since:
            query = query.where(LedgerEntryModel.created_at >= since)

        result = await self.session.execute(query)
        return abs(result.scalar() or Decimal("0"))

    async def get_revenue_stats(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get revenue statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total deposits
        deposits = await self.get_total_by_type(LedgerEntryType.DEPOSIT, since)

        # Total spent (generations)
        spent = await self.get_total_by_type(LedgerEntryType.GENERATION, since)

        # Admin adjustments
        admin_add = await self.get_total_by_type(LedgerEntryType.ADMIN_ADJUSTMENT, since)

        # Referral bonuses
        referral = await self.get_total_by_type(LedgerEntryType.REFERRAL_BONUS, since)

        # Refunds
        refunds = await self.get_total_by_type(LedgerEntryType.REFUND, since)

        return {
            "period_days": days,
            "total_deposits": float(deposits),
            "total_spent": float(spent),
            "admin_adjustments": float(admin_add),
            "referral_bonuses": float(referral),
            "refunds": float(refunds),
            "net_revenue": float(deposits - refunds),
        }

    async def get_daily_revenue(
        self,
        days: int = 7,
    ) -> Sequence[Dict[str, Any]]:
        """Get daily revenue statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(LedgerEntryModel.created_at).label("date"),
                func.sum(
                    func.case(
                        (LedgerEntryModel.entry_type == LedgerEntryType.DEPOSIT.value, LedgerEntryModel.amount),
                        else_=Decimal("0"),
                    )
                ).label("deposits"),
                func.sum(
                    func.case(
                        (
                            LedgerEntryModel.entry_type == LedgerEntryType.GENERATION.value,
                            func.abs(LedgerEntryModel.amount),
                        ),
                        else_=Decimal("0"),
                    )
                ).label("spent"),
            )
            .where(LedgerEntryModel.created_at >= since)
            .group_by(func.date(LedgerEntryModel.created_at))
            .order_by(func.date(LedgerEntryModel.created_at))
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "deposits": float(row.deposits or 0),
                "spent": float(row.spent or 0),
            }
            for row in result.all()
        ]

    async def get_user_stats(
        self,
        telegram_id: int,
    ) -> Dict[str, Any]:
        """Get user's ledger statistics."""
        balance = await self.get_balance(telegram_id)

        # Total deposited
        deposit_query = select(func.coalesce(func.sum(LedgerEntryModel.amount), Decimal("0"))).where(
            and_(
                LedgerEntryModel.telegram_id == telegram_id,
                LedgerEntryModel.entry_type == LedgerEntryType.DEPOSIT.value,
            )
        )
        deposit_result = await self.session.execute(deposit_query)
        total_deposited = deposit_result.scalar() or Decimal("0")

        # Total spent
        spent_query = select(func.coalesce(func.sum(func.abs(LedgerEntryModel.amount)), Decimal("0"))).where(
            and_(
                LedgerEntryModel.telegram_id == telegram_id,
                LedgerEntryModel.entry_type == LedgerEntryType.GENERATION.value,
            )
        )
        spent_result = await self.session.execute(spent_query)
        total_spent = spent_result.scalar() or Decimal("0")

        # Referral earnings
        referral_query = select(func.coalesce(func.sum(LedgerEntryModel.amount), Decimal("0"))).where(
            and_(
                LedgerEntryModel.telegram_id == telegram_id,
                LedgerEntryModel.entry_type == LedgerEntryType.REFERRAL_BONUS.value,
            )
        )
        referral_result = await self.session.execute(referral_query)
        referral_earnings = referral_result.scalar() or Decimal("0")

        return {
            "balance": float(balance),
            "total_deposited": float(total_deposited),
            "total_spent": float(total_spent),
            "referral_earnings": float(referral_earnings),
        }
