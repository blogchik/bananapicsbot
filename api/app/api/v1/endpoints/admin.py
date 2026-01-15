"""Admin endpoints for bot administration."""
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_async_session
from app.schemas.admin import (
    # Credits
    AdminCreditIn,
    AdminCreditOut,
    # Users
    AdminUserOut,
    UserListOut,
    # Stats
    DashboardStatsOut,
)
from app.services.admin_service import AdminService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin")


# ============ Dashboard Stats ============

@router.get("/stats", response_model=DashboardStatsOut)
async def get_dashboard_stats(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
):
    """Get admin dashboard statistics."""
    try:
        service = AdminService(session)
        
        user_stats = await service.get_user_stats()
        gen_stats = await service.get_generation_stats(days)
        revenue_stats = await service.get_revenue_stats(days)
        payment_stats = await service.get_payment_stats(days)
        
        return DashboardStatsOut(
            total_users=user_stats["total_users"],
            active_users_7d=user_stats["active_7d"],
            active_users_30d=user_stats["active_30d"],
            new_users_today=user_stats["new_today"],
            banned_users=user_stats["banned_users"],
            total_generations=gen_stats["total_generations"],
            completed_generations=gen_stats["completed"],
            failed_generations=gen_stats["failed"],
            success_rate=gen_stats["success_rate"],
            total_deposits=revenue_stats["total_deposits"],
            total_spent=revenue_stats["total_spent"],
            net_revenue=revenue_stats["net_revenue"],
            total_payments=payment_stats["total_payments"],
            completed_payments=payment_stats["completed_payments"],
            payment_success_rate=payment_stats["success_rate"],
        )
    except Exception as e:
        logger.exception("Failed to get dashboard stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ User Management ============

@router.get("/users", response_model=UserListOut)
async def search_users(
    query: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """Search users with filters."""
    try:
        service = AdminService(session)
        
        users, total = await service.search_users(
            query=query,
            offset=offset,
            limit=limit,
        )
        
        result_users = []
        for user in users:
            balance = await service.get_user_balance(user.id)
            referral_count = await service.get_user_referral_count(user.id)
            gen_count = await service.get_user_generation_count(user.id)
            
            result_users.append(AdminUserOut(
                telegram_id=user.telegram_id,
                username=None,
                first_name=None,
                last_name=None,
                language_code="uz",
                is_active=True,
                is_banned=False,
                ban_reason=None,
                trial_remaining=3,
                balance=Decimal(balance),
                referrer_id=user.referred_by_id,
                referral_count=referral_count,
                generation_count=gen_count,
                created_at=user.created_at,
                last_active_at=None,
            ))
        
        return UserListOut(
            users=result_users,
            total=total,
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        logger.exception("Failed to search users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/users/{telegram_id}", response_model=AdminUserOut)
async def get_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get user details."""
    try:
        service = AdminService(session)
        
        user = await service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        balance = await service.get_user_balance(user.id)
        referral_count = await service.get_user_referral_count(user.id)
        gen_count = await service.get_user_generation_count(user.id)
        
        return AdminUserOut(
            telegram_id=user.telegram_id,
            username=None,
            first_name=None,
            last_name=None,
            language_code="uz",
            is_active=True,
            is_banned=False,
            ban_reason=None,
            trial_remaining=3,
            balance=Decimal(balance),
            referrer_id=user.referred_by_id,
            referral_count=referral_count,
            generation_count=gen_count,
            created_at=user.created_at,
            last_active_at=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ Credits Management ============

@router.post("/credits", response_model=AdminCreditOut)
async def adjust_credits(
    data: AdminCreditIn,
    session: AsyncSession = Depends(get_async_session),
):
    """Add or remove credits from user."""
    try:
        service = AdminService(session)
        
        user = await service.get_user_by_telegram_id(data.telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_balance = await service.get_user_balance(user.id)
        
        await service.add_user_credits(
            user_id=user.id,
            amount=data.amount,
            reason=data.reason or "Admin adjustment",
        )
        
        new_balance = await service.get_user_balance(user.id)
        
        return AdminCreditOut(
            telegram_id=data.telegram_id,
            amount=data.amount,
            old_balance=old_balance,
            new_balance=new_balance,
            reason=data.reason,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to adjust credits", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ Health Check ============

@router.get("/health")
async def health_check():
    """Admin API health check."""
    return {"status": "ok"}

