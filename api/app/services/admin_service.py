"""Admin service for dashboard and statistics."""
from typing import Optional, Dict, Any, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    User,
    GenerationRequest,
    GenerationStatus,
    LedgerEntry,
    ModelCatalog,
    ModelPrice,
)


class AdminService:
    """Admin dashboard service."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ============ User Stats ============
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        # Total users
        total_query = select(func.count()).select_from(User)
        total_result = await self.session.execute(total_query)
        total_users = total_result.scalar() or 0
        
        # New today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today_query = select(func.count()).select_from(User).where(
            User.created_at >= today
        )
        new_today_result = await self.session.execute(new_today_query)
        new_today = new_today_result.scalar() or 0
        
        # Active 7 days (has generations)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_7d_query = select(func.count(func.distinct(GenerationRequest.user_id))).where(
            GenerationRequest.created_at >= week_ago
        )
        active_7d_result = await self.session.execute(active_7d_query)
        active_7d = active_7d_result.scalar() or 0
        
        # Active 30 days
        month_ago = datetime.utcnow() - timedelta(days=30)
        active_30d_query = select(func.count(func.distinct(GenerationRequest.user_id))).where(
            GenerationRequest.created_at >= month_ago
        )
        active_30d_result = await self.session.execute(active_30d_query)
        active_30d = active_30d_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "new_today": new_today,
            "active_7d": active_7d,
            "active_30d": active_30d,
            "banned_users": 0,  # Not tracked in current schema
        }
    
    # ============ Generation Stats ============
    
    async def get_generation_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get generation statistics."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Total generations
        total_query = select(func.count()).select_from(GenerationRequest).where(
            GenerationRequest.created_at >= since
        )
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0
        
        # Completed
        completed_query = select(func.count()).select_from(GenerationRequest).where(
            and_(
                GenerationRequest.created_at >= since,
                GenerationRequest.status == GenerationStatus.completed,
            )
        )
        completed_result = await self.session.execute(completed_query)
        completed = completed_result.scalar() or 0
        
        # Failed
        failed_query = select(func.count()).select_from(GenerationRequest).where(
            and_(
                GenerationRequest.created_at >= since,
                GenerationRequest.status == GenerationStatus.failed,
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
        """Get revenue statistics."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Total deposits
        deposit_query = select(
            func.coalesce(func.sum(LedgerEntry.amount), 0)
        ).where(
            and_(
                LedgerEntry.created_at >= since,
                LedgerEntry.entry_type == "deposit",
            )
        )
        deposit_result = await self.session.execute(deposit_query)
        deposits = deposit_result.scalar() or 0
        
        # Total spent (generations - negative values)
        spent_query = select(
            func.coalesce(func.abs(func.sum(LedgerEntry.amount)), 0)
        ).where(
            and_(
                LedgerEntry.created_at >= since,
                LedgerEntry.entry_type == "generation",
            )
        )
        spent_result = await self.session.execute(spent_query)
        spent = spent_result.scalar() or 0
        
        return {
            "total_deposits": deposits,
            "total_spent": spent,
            "net_revenue": deposits,
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
        query = select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_user_generation_count(self, user_id: int) -> int:
        """Get user's generation count."""
        query = select(func.count()).select_from(GenerationRequest).where(
            GenerationRequest.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_user_referral_count(self, user_id: int) -> int:
        """Get user's referral count."""
        query = select(func.count()).select_from(User).where(
            User.referred_by_id == user_id
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
    
    # ============ Daily Stats ============
    
    async def get_daily_generation_stats(self, days: int = 7) -> Sequence[Dict[str, Any]]:
        """Get daily generation statistics."""
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
        return [
            {"date": str(row.date), "count": row.count}
            for row in result.all()
        ]
