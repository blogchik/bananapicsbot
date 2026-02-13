"""Admin service for dashboard and statistics."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    LedgerEntry,
    ModelCatalog,
    ModelPrice,
    PaymentLedger,
    User,
)


class AdminService:
    """Admin dashboard service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============ User Stats ============

    async def get_user_stats(self) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        now = datetime.utcnow()

        # Total users
        total_query = select(func.count()).select_from(User)
        total_result = await self.session.execute(total_query)
        total_users = total_result.scalar() or 0

        # New today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        new_today_query = select(func.count()).select_from(User).where(User.created_at >= today_start)
        new_today_result = await self.session.execute(new_today_query)
        new_today = new_today_result.scalar() or 0

        # New this week
        week_ago = now - timedelta(days=7)
        new_week_query = select(func.count()).select_from(User).where(User.created_at >= week_ago)
        new_week_result = await self.session.execute(new_week_query)
        new_week = new_week_result.scalar() or 0

        # New this month
        month_ago = now - timedelta(days=30)
        new_month_query = select(func.count()).select_from(User).where(User.created_at >= month_ago)
        new_month_result = await self.session.execute(new_month_query)
        new_month = new_month_result.scalar() or 0

        # Active 7 days (has generations)
        active_7d_query = select(func.count(func.distinct(GenerationRequest.user_id))).where(
            GenerationRequest.created_at >= week_ago
        )
        active_7d_result = await self.session.execute(active_7d_query)
        active_7d = active_7d_result.scalar() or 0

        # Active 30 days
        active_30d_query = select(func.count(func.distinct(GenerationRequest.user_id))).where(
            GenerationRequest.created_at >= month_ago
        )
        active_30d_result = await self.session.execute(active_30d_query)
        active_30d = active_30d_result.scalar() or 0

        return {
            "total_users": total_users,
            "new_today": new_today,
            "new_week": new_week,
            "new_month": new_month,
            "active_7d": active_7d,
            "active_30d": active_30d,
            "banned_users": 0,  # Not tracked in current schema
        }

    # ============ Generation Stats ============

    async def get_generation_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get generation statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total generations
        total_query = select(func.count()).select_from(GenerationRequest).where(GenerationRequest.created_at >= since)
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0

        # Completed
        completed_query = (
            select(func.count())
            .select_from(GenerationRequest)
            .where(
                and_(
                    GenerationRequest.created_at >= since,
                    GenerationRequest.status == GenerationStatus.completed,
                )
            )
        )
        completed_result = await self.session.execute(completed_query)
        completed = completed_result.scalar() or 0

        # Failed
        failed_query = (
            select(func.count())
            .select_from(GenerationRequest)
            .where(
                and_(
                    GenerationRequest.created_at >= since,
                    GenerationRequest.status == GenerationStatus.failed,
                )
            )
        )
        failed_result = await self.session.execute(failed_query)
        failed = failed_result.scalar() or 0

        success_rate = (completed / total * 100) if total > 0 else 0.0

        return {
            "total_generations": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(success_rate, 2),
        }

    # ============ Revenue Stats ============

    async def get_revenue_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue statistics - returns stars (not credits)."""
        now = datetime.utcnow()
        since = now - timedelta(days=days)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        # Helper to get stars paid for a period from PaymentLedger (excluding refunded)
        async def get_stars_since(start_date: datetime) -> float:
            query = select(func.coalesce(func.sum(PaymentLedger.stars_amount), 0)).where(
                and_(
                    PaymentLedger.created_at >= start_date,
                    PaymentLedger.is_refunded == False,  # Exclude refunded payments
                )
            )
            result = await self.session.execute(query)
            return float(result.scalar() or 0)

        # Helper to get refunded stars for a period
        async def get_refunded_since(start_date: datetime) -> float:
            query = select(func.coalesce(func.sum(PaymentLedger.stars_amount), 0)).where(
                and_(
                    PaymentLedger.created_at >= start_date,
                    PaymentLedger.is_refunded == True,
                )
            )
            result = await self.session.execute(query)
            return float(result.scalar() or 0)

        # Total stars received (excluding refunded)
        total_stars = await get_stars_since(since)
        today_stars = await get_stars_since(today_start)
        week_stars = await get_stars_since(week_start)
        month_stars = await get_stars_since(month_start)

        # Total refunded stars
        total_refunded = await get_refunded_since(since)

        # Total credits spent (generations - negative values)
        spent_query = select(func.coalesce(func.abs(func.sum(LedgerEntry.amount)), 0)).where(
            and_(
                LedgerEntry.created_at >= since,
                LedgerEntry.entry_type == "generation",
            )
        )
        spent_result = await self.session.execute(spent_query)
        spent = spent_result.scalar() or 0

        # Get by_model statistics with credits
        by_model_query = (
            select(
                ModelCatalog.key,
                func.count(GenerationRequest.id).label("count"),
                func.coalesce(func.sum(GenerationRequest.cost), 0).label("credits"),
            )
            .join(ModelCatalog, GenerationRequest.model_id == ModelCatalog.id)
            .where(
                and_(
                    GenerationRequest.created_at >= since,
                    GenerationRequest.status == GenerationStatus.completed,
                )
            )
            .group_by(ModelCatalog.key)
        )
        by_model_result = await self.session.execute(by_model_query)
        by_model = {row.key: {"count": row.count, "credits": int(row.credits)} for row in by_model_result.all()}

        return {
            "total_deposits": total_stars,
            "today_deposits": today_stars,
            "week_deposits": week_stars,
            "month_deposits": month_stars,
            "total_refunded": total_refunded,
            "total_spent": spent,
            "net_revenue": total_stars,
            "by_model": by_model,
        }

    # ============ Payment Stats ============

    async def get_payment_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get payment statistics - placeholder since no payment table yet."""
        return {
            "total_payments": 0,
            "completed_payments": 0,
            "success_rate": 0.0,
        }

    # ============ User Search ============

    async def search_users(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[User], int]:
        """Search users with filters."""
        base_query = select(User)

        if query:
            # Try to search by telegram_id
            try:
                tid = int(query)
                base_query = base_query.where(User.telegram_id == tid)
            except ValueError:
                # Search by referral_code
                base_query = base_query.where(User.referral_code.ilike(f"%{query}%"))

        # Count total
        count_query = select(func.count()).select_from(User)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get page
        base_query = base_query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(base_query)
        users = result.scalars().all()

        return users, total

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID."""
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_balance(self, user_id: int) -> int:
        """Get user balance."""
        query = select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(LedgerEntry.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_generation_count(self, user_id: int) -> int:
        """Get user's generation count."""
        query = select(func.count()).select_from(GenerationRequest).where(GenerationRequest.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_referral_count(self, user_id: int) -> int:
        """Get user's referral count."""
        query = select(func.count()).select_from(User).where(User.referred_by_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_trial_used(self, user_id: int) -> int:
        """Get user's trial generations used count."""
        from app.db.models import TrialUse

        query = select(func.count()).select_from(TrialUse).where(TrialUse.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_total_spent(self, user_id: int) -> int:
        """Get user's total credits spent on generations."""
        query = select(func.coalesce(func.abs(func.sum(LedgerEntry.amount)), 0)).where(
            and_(
                LedgerEntry.user_id == user_id,
                LedgerEntry.entry_type == "generation",
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_total_deposits(self, user_id: int) -> int:
        """Get user's total deposits (stars paid)."""
        query = select(func.coalesce(func.sum(PaymentLedger.stars_amount), 0)).where(
            and_(
                PaymentLedger.user_id == user_id,
                PaymentLedger.is_refunded.is_(False),
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    # ============ Credits Management ============

    async def add_user_credits(
        self,
        user_id: int,
        amount: int,
        reason: str = "Admin adjustment",
    ) -> LedgerEntry:
        """Add credits to user."""
        entry = LedgerEntry(
            user_id=user_id,
            amount=amount,
            entry_type="admin_adjustment",
            description=reason,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    # ============ Chart Data ============

    async def get_daily_users(self, days: int = 30) -> Sequence[Dict[str, Any]]:
        """Get daily new user registrations."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(User.created_at).label("date"),
                func.count().label("count"),
            )
            .where(User.created_at >= since)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
        )

        result = await self.session.execute(query)
        return [{"date": str(row.date), "count": row.count} for row in result.all()]

    async def get_daily_generations(self, days: int = 30) -> Sequence[Dict[str, Any]]:
        """Get daily generation stats (total, completed, failed)."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(GenerationRequest.created_at).label("date"),
                func.count().label("total"),
                func.count().filter(GenerationRequest.status == GenerationStatus.completed).label("completed"),
                func.count().filter(GenerationRequest.status == GenerationStatus.failed).label("failed"),
            )
            .where(GenerationRequest.created_at >= since)
            .group_by(func.date(GenerationRequest.created_at))
            .order_by(func.date(GenerationRequest.created_at))
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "total": row.total,
                "completed": row.completed,
                "failed": row.failed,
            }
            for row in result.all()
        ]

    async def get_daily_revenue(self, days: int = 30) -> Sequence[Dict[str, Any]]:
        """Get daily revenue (stars)."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(PaymentLedger.created_at).label("date"),
                func.coalesce(func.sum(PaymentLedger.stars_amount), 0).label("amount"),
                func.count().label("count"),
            )
            .where(
                and_(
                    PaymentLedger.created_at >= since,
                    PaymentLedger.is_refunded == False,
                )
            )
            .group_by(func.date(PaymentLedger.created_at))
            .order_by(func.date(PaymentLedger.created_at))
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "amount": float(row.amount),
                "count": row.count,
            }
            for row in result.all()
        ]

    async def get_models_breakdown(self, days: int = 30) -> Sequence[Dict[str, Any]]:
        """Get generation count and credits by model."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ModelCatalog.key.label("model_key"),
                ModelCatalog.name.label("model_name"),
                func.count(GenerationRequest.id).label("count"),
                func.coalesce(func.sum(GenerationRequest.cost), 0).label("credits"),
            )
            .join(ModelCatalog, GenerationRequest.model_id == ModelCatalog.id)
            .where(
                and_(
                    GenerationRequest.created_at >= since,
                    GenerationRequest.status == GenerationStatus.completed,
                )
            )
            .group_by(ModelCatalog.key, ModelCatalog.name)
            .order_by(func.count(GenerationRequest.id).desc())
        )

        result = await self.session.execute(query)
        return [
            {
                "model_key": row.model_key,
                "model_name": row.model_name,
                "count": row.count,
                "credits": int(row.credits),
            }
            for row in result.all()
        ]

    async def get_daily_generation_stats(self, days: int = 7) -> Sequence[Dict[str, Any]]:
        """Get daily generation statistics (legacy)."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(GenerationRequest.created_at).label("date"),
                func.count().label("count"),
            )
            .where(GenerationRequest.created_at >= since)
            .group_by(func.date(GenerationRequest.created_at))
            .order_by(func.date(GenerationRequest.created_at))
        )

        result = await self.session.execute(query)
        return [{"date": str(row.date), "count": row.count} for row in result.all()]

    # ============ User Generations ============

    async def get_user_generations(
        self,
        user_id: int,
        limit: int = 10,
    ) -> Sequence[Dict[str, Any]]:
        """Get user's recent generations."""
        query = (
            select(GenerationRequest)
            .where(GenerationRequest.user_id == user_id)
            .order_by(GenerationRequest.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        generations = result.scalars().all()

        items = []
        for gen in generations:
            # Get model info
            model_name = "Unknown"
            model_key = "unknown"
            if gen.model_id:
                model_query = select(ModelCatalog).where(ModelCatalog.id == gen.model_id)
                model_result = await self.session.execute(model_query)
                model = model_result.scalar_one_or_none()
                if model:
                    model_name = model.name
                    model_key = model.key

            # Get result images
            result_query = select(GenerationResult).where(GenerationResult.request_id == gen.id).limit(4)
            result_res = await self.session.execute(result_query)
            results = result_res.scalars().all()
            result_urls = [r.image_url for r in results if r.image_url]

            items.append(
                {
                    "id": gen.id,
                    "public_id": gen.public_id,
                    "model_key": model_key,
                    "model_name": model_name,
                    "prompt": gen.prompt[:100] if gen.prompt else "",
                    "full_prompt": gen.prompt or "",
                    "status": gen.status.value if gen.status else "unknown",
                    "cost": gen.cost,
                    "result_urls": result_urls,
                    "created_at": gen.created_at.isoformat() if gen.created_at else None,
                    "completed_at": gen.completed_at.isoformat() if gen.completed_at else None,
                }
            )

        return items

    # ============ Refund Generation ============

    async def refund_generation(
        self,
        user_id: int,
        generation_id: int,
    ) -> Dict[str, Any]:
        """Refund a specific generation."""
        # Find generation
        query = select(GenerationRequest).where(
            and_(
                GenerationRequest.id == generation_id,
                GenerationRequest.user_id == user_id,
            )
        )
        result = await self.session.execute(query)
        generation = result.scalar_one_or_none()

        if not generation:
            return {"error": True, "message": "Generation not found"}

        # Find associated ledger entry
        ledger_query = select(LedgerEntry).where(
            and_(
                LedgerEntry.user_id == user_id,
                LedgerEntry.entry_type == "generation",
                LedgerEntry.reference_id.contains(str(generation_id)),
            )
        )
        ledger_result = await self.session.execute(ledger_query)
        ledger_entry = ledger_result.scalar_one_or_none()

        refund_amount = 0
        if ledger_entry:
            refund_amount = abs(ledger_entry.amount)
        else:
            # Estimate from model price
            if generation.model_id:
                price_query = select(ModelPrice).where(ModelPrice.model_id == generation.model_id)
                price_result = await self.session.execute(price_query)
                price = price_result.scalar_one_or_none()
                if price:
                    refund_amount = price.credits

        if refund_amount > 0:
            # Create refund entry
            refund_entry = LedgerEntry(
                user_id=user_id,
                amount=refund_amount,
                entry_type="refund",
                description=f"Refund for generation {generation_id}",
                reference_id=f"refund_{generation_id}",
            )
            self.session.add(refund_entry)
            await self.session.commit()

        new_balance = await self.get_user_balance(user_id)

        return {
            "credits_refunded": refund_amount,
            "new_balance": new_balance,
        }

    # ============ User Payments ============

    # ============ Model Management ============

    async def get_all_models(self) -> Sequence[Dict[str, Any]]:
        """Get all models with prices and generation counts."""
        query = select(ModelCatalog).options(selectinload(ModelCatalog.prices)).order_by(ModelCatalog.name)
        result = await self.session.execute(query)
        models = result.scalars().all()

        items = []
        for model in models:
            # Get generation count
            gen_count_query = (
                select(func.count()).select_from(GenerationRequest).where(GenerationRequest.model_id == model.id)
            )
            gen_count_result = await self.session.execute(gen_count_query)
            gen_count = gen_count_result.scalar() or 0

            active_price = next((p for p in model.prices if p.is_active), None)

            items.append(
                {
                    "id": model.id,
                    "key": model.key,
                    "name": model.name,
                    "provider": model.provider,
                    "is_active": model.is_active,
                    "supports_text_to_image": model.supports_text_to_image,
                    "supports_image_to_image": model.supports_image_to_image,
                    "supports_reference": model.supports_reference,
                    "supports_aspect_ratio": model.supports_aspect_ratio,
                    "supports_style": model.supports_style,
                    "generation_count": gen_count,
                    "prices": [
                        {
                            "id": p.id,
                            "unit_price": p.unit_price,
                            "currency": p.currency,
                            "is_active": p.is_active,
                        }
                        for p in model.prices
                    ],
                    "current_price": active_price.unit_price if active_price else 0,
                }
            )

        return items

    async def update_model(self, model_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update model fields (is_active, name)."""
        query = select(ModelCatalog).where(ModelCatalog.id == model_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        if "is_active" in data:
            model.is_active = data["is_active"]
        if "name" in data:
            model.name = data["name"]

        await self.session.commit()
        return {"id": model.id, "key": model.key, "name": model.name, "is_active": model.is_active}

    async def update_model_price(self, model_id: int, unit_price: int) -> Optional[Dict[str, Any]]:
        """Update model price (deactivate old, create new)."""
        # Verify model exists
        model_query = select(ModelCatalog).where(ModelCatalog.id == model_id)
        model_result = await self.session.execute(model_query)
        model = model_result.scalar_one_or_none()

        if not model:
            return None

        # Deactivate existing active prices
        await self.session.execute(
            update(ModelPrice)
            .where(and_(ModelPrice.model_id == model_id, ModelPrice.is_active == True))
            .values(is_active=False)
        )

        # Create new price
        new_price = ModelPrice(model_id=model_id, unit_price=unit_price, currency="credit", is_active=True)
        self.session.add(new_price)
        await self.session.commit()

        return {"model_id": model_id, "unit_price": unit_price, "price_id": new_price.id}

    # ============ Global Payments ============

    async def get_global_payments(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Dict[str, Any]], int]:
        """Get all payments with pagination."""
        # Count
        count_query = select(func.count()).select_from(PaymentLedger)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get payments with user info
        query = (
            select(PaymentLedger, User.telegram_id)
            .join(User, PaymentLedger.user_id == User.id)
            .order_by(PaymentLedger.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()

        items = []
        for payment, telegram_id in rows:
            items.append(
                {
                    "id": payment.id,
                    "telegram_id": telegram_id,
                    "provider": payment.provider,
                    "currency": payment.currency,
                    "stars_amount": payment.stars_amount,
                    "credits_amount": payment.credits_amount,
                    "telegram_charge_id": payment.telegram_charge_id,
                    "is_refunded": payment.is_refunded,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                }
            )

        return items, total

    async def get_payment_daily_stats(self, days: int = 30) -> Sequence[Dict[str, Any]]:
        """Get daily payment stats."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(PaymentLedger.created_at).label("date"),
                func.count().label("count"),
                func.coalesce(func.sum(PaymentLedger.stars_amount), 0).label("stars"),
                func.coalesce(func.sum(PaymentLedger.credits_amount), 0).label("credits"),
            )
            .where(PaymentLedger.created_at >= since)
            .group_by(func.date(PaymentLedger.created_at))
            .order_by(func.date(PaymentLedger.created_at))
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "count": row.count,
                "stars": int(row.stars),
                "credits": int(row.credits),
            }
            for row in result.all()
        ]

    # ============ Global Generations ============

    async def get_global_generations(
        self,
        offset: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
    ) -> tuple[Sequence[Dict[str, Any]], int]:
        """Get all generations with pagination and optional status filter."""
        base_filter = []
        if status_filter:
            try:
                gen_status = GenerationStatus(status_filter)
                base_filter.append(GenerationRequest.status == gen_status)
            except ValueError:
                pass

        # Count
        count_query = select(func.count()).select_from(GenerationRequest)
        if base_filter:
            count_query = count_query.where(*base_filter)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get generations with user and model info
        query = (
            select(
                GenerationRequest,
                User.telegram_id,
                ModelCatalog.name.label("model_name"),
                ModelCatalog.key.label("model_key"),
            )
            .join(User, GenerationRequest.user_id == User.id)
            .join(ModelCatalog, GenerationRequest.model_id == ModelCatalog.id)
        )
        if base_filter:
            query = query.where(*base_filter)
        query = query.order_by(GenerationRequest.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        rows = result.all()

        items = []
        for gen, telegram_id, model_name, model_key in rows:
            # Get result images
            result_query = select(GenerationResult).where(GenerationResult.request_id == gen.id).limit(4)
            result_res = await self.session.execute(result_query)
            results = result_res.scalars().all()
            result_urls = [r.image_url for r in results if r.image_url]

            items.append(
                {
                    "id": gen.id,
                    "public_id": gen.public_id,
                    "telegram_id": telegram_id,
                    "model_name": model_name,
                    "model_key": model_key,
                    "prompt": gen.prompt[:100] if gen.prompt else "",
                    "full_prompt": gen.prompt,
                    "status": gen.status.value if gen.status else "unknown",
                    "cost": gen.cost,
                    "result_urls": result_urls,
                    "created_at": gen.created_at.isoformat() if gen.created_at else None,
                    "completed_at": gen.completed_at.isoformat() if gen.completed_at else None,
                }
            )

        return items, total

    async def get_generation_queue_status(self) -> Dict[str, int]:
        """Get current generation queue counts by status."""
        query = (
            select(
                GenerationRequest.status,
                func.count().label("count"),
            )
            .where(
                GenerationRequest.status.in_(
                    [
                        GenerationStatus.pending,
                        GenerationStatus.queued,
                        GenerationStatus.running,
                        GenerationStatus.configuring,
                    ]
                )
            )
            .group_by(GenerationRequest.status)
        )
        result = await self.session.execute(query)
        rows = result.all()

        status_counts = {
            "pending": 0,
            "configuring": 0,
            "queued": 0,
            "running": 0,
        }
        for row_status, count in rows:
            status_counts[row_status.value] = count

        return status_counts

    # ============ User Payments ============

    async def get_user_payments(
        self,
        user_id: int,
        limit: int = 10,
    ) -> Sequence[Dict[str, Any]]:
        """Get user's payment history."""
        from app.db.models import PaymentLedger

        query = (
            select(PaymentLedger)
            .where(PaymentLedger.user_id == user_id)
            .order_by(PaymentLedger.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        payments = result.scalars().all()

        items = []
        for payment in payments:
            items.append(
                {
                    "id": payment.id,
                    "provider": payment.provider,
                    "currency": payment.currency,
                    "stars_amount": payment.stars_amount,
                    "credits_amount": payment.credits_amount,
                    "telegram_charge_id": payment.telegram_charge_id,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                }
            )

        return items
