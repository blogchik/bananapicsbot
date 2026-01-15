"""Admin use cases."""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.entities.broadcast import Broadcast, BroadcastStatus, BroadcastContentType
from app.domain.interfaces.repositories import (
    IUserRepository,
    IGenerationRepository,
    ILedgerRepository,
    IPaymentRepository,
    IBroadcastRepository,
)
from app.domain.interfaces.services import ICacheService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DashboardStats:
    """Admin dashboard statistics."""
    # Users
    total_users: int
    active_users_7d: int
    active_users_30d: int
    new_users_today: int
    banned_users: int
    
    # Generations
    total_generations: int
    completed_generations: int
    failed_generations: int
    success_rate: float
    
    # Revenue
    total_deposits: float
    total_spent: float
    net_revenue: float
    
    # Payments
    total_payments: int
    completed_payments: int
    payment_success_rate: float


class GetStatsUseCase:
    """Get admin dashboard statistics."""
    
    def __init__(
        self,
        user_repo: IUserRepository,
        generation_repo: IGenerationRepository,
        ledger_repo: ILedgerRepository,
        payment_repo: IPaymentRepository,
        cache: ICacheService,
    ):
        self._user_repo = user_repo
        self._generation_repo = generation_repo
        self._ledger_repo = ledger_repo
        self._payment_repo = payment_repo
        self._cache = cache
    
    async def execute(self, days: int = 30) -> DashboardStats:
        """Execute use case."""
        # Try cache first (1 minute TTL)
        cache_key = f"admin_stats:{days}"
        cached = await self._cache.get(cache_key)
        if cached:
            return DashboardStats(**cached)
        
        # Get all stats
        user_stats = await self._user_repo.get_stats()
        gen_stats = await self._generation_repo.get_stats(days)
        revenue_stats = await self._ledger_repo.get_revenue_stats(days)
        payment_stats = await self._payment_repo.get_stats(days)
        
        result = DashboardStats(
            # Users
            total_users=user_stats["total_users"],
            active_users_7d=user_stats["active_7d"],
            active_users_30d=user_stats["active_30d"],
            new_users_today=user_stats["new_today"],
            banned_users=user_stats["banned_users"],
            
            # Generations
            total_generations=gen_stats["total_generations"],
            completed_generations=gen_stats["completed"],
            failed_generations=gen_stats["failed"],
            success_rate=gen_stats["success_rate"],
            
            # Revenue
            total_deposits=revenue_stats["total_deposits"],
            total_spent=revenue_stats["total_spent"],
            net_revenue=revenue_stats["net_revenue"],
            
            # Payments
            total_payments=payment_stats["total_payments"],
            completed_payments=payment_stats["completed_payments"],
            payment_success_rate=payment_stats["success_rate"],
        )
        
        # Cache for 1 minute
        await self._cache.set(cache_key, result.__dict__, ttl=60)
        
        return result


class CreateBroadcastUseCase:
    """Create broadcast message."""
    
    def __init__(
        self,
        broadcast_repo: IBroadcastRepository,
        user_repo: IUserRepository,
    ):
        self._broadcast_repo = broadcast_repo
        self._user_repo = user_repo
    
    async def execute(
        self,
        admin_id: int,
        content_type: BroadcastContentType,
        content: str,
        media_file_id: Optional[str] = None,
    ) -> Broadcast:
        """Execute use case."""
        # Get total recipients (active users)
        total_recipients = await self._user_repo.count_total()
        
        # Create broadcast
        broadcast = await self._broadcast_repo.create(
            admin_id=admin_id,
            content_type=content_type,
            content=content,
            media_file_id=media_file_id,
            total_recipients=total_recipients,
        )
        
        logger.info(
            "Broadcast created",
            broadcast_id=str(broadcast.id),
            admin_id=admin_id,
            total_recipients=total_recipients,
        )
        
        return broadcast


class GetDailyReportUseCase:
    """Get daily report for admin."""
    
    def __init__(
        self,
        user_repo: IUserRepository,
        generation_repo: IGenerationRepository,
        ledger_repo: ILedgerRepository,
        payment_repo: IPaymentRepository,
    ):
        self._user_repo = user_repo
        self._generation_repo = generation_repo
        self._ledger_repo = ledger_repo
        self._payment_repo = payment_repo
    
    async def execute(self, days: int = 7) -> Dict[str, Any]:
        """Execute use case."""
        return {
            "user_stats": await self._user_repo.get_stats(),
            "generation_daily": await self._generation_repo.get_daily_stats(days),
            "revenue_daily": await self._ledger_repo.get_daily_revenue(days),
            "payment_daily": await self._payment_repo.get_daily_stats(days),
        }
