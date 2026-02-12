"""Admin endpoints for bot administration."""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.deps.admin_auth import require_admin
from app.deps.db import get_async_session
from app.infrastructure.logging import get_logger
from app.schemas.admin import (
    AdminCreditIn,
    AdminCreditOut,
    AdminInfo,
    AdminLoginResponse,
    AdminUserOut,
    BroadcastCreateRequest,
    BroadcastListOut,
    BroadcastOut,
    BroadcastStatusOut,
    DashboardStatsOut,
    TelegramLoginData,
    UserListOut,
)
from app.services.admin_auth import create_admin_token, verify_telegram_login
from app.services.admin_service import AdminService
from app.services.broadcast_service import BroadcastService

logger = get_logger(__name__)

router = APIRouter(prefix="/admin")


# ============ Auth (no auth required) ============


@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(data: TelegramLoginData):
    """Authenticate admin via Telegram Login Widget."""
    settings = get_settings()

    if not settings.bot_token:
        raise HTTPException(status_code=500, detail="Bot token not configured")

    if not settings.admin_jwt_secret:
        raise HTTPException(status_code=500, detail="Admin JWT secret not configured")

    # Verify Telegram Login Widget hash
    login_data = data.model_dump()
    if not verify_telegram_login(login_data, settings.bot_token):
        raise HTTPException(status_code=401, detail="Invalid Telegram login data")

    # Check if user is admin
    if data.id not in settings.admin_ids_list:
        raise HTTPException(status_code=403, detail="You are not an admin")

    # Create JWT token
    token, expires_at = create_admin_token(
        telegram_id=data.id,
        username=data.username,
        first_name=data.first_name,
    )

    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        admin=AdminInfo(
            telegram_id=data.id,
            username=data.username,
            first_name=data.first_name,
        ),
        expires_at=expires_at,
    )


@router.get("/auth/me", response_model=AdminInfo)
async def admin_me(admin: dict = Depends(require_admin)):
    """Get current admin info from JWT."""
    return AdminInfo(
        telegram_id=admin["telegram_id"],
        username=admin.get("username"),
        first_name=admin.get("first_name", "Admin"),
    )


# ============ Health Check (no auth required) ============


@router.get("/health")
async def health_check():
    """Admin API health check."""
    return {"status": "ok"}


# ============ Dashboard Stats ============


@router.get("/stats", response_model=DashboardStatsOut)
async def get_dashboard_stats(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
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
            new_users_week=user_stats["new_week"],
            new_users_month=user_stats["new_month"],
            banned_users=user_stats["banned_users"],
            total_generations=gen_stats["total_generations"],
            completed_generations=gen_stats["completed"],
            failed_generations=gen_stats["failed"],
            success_rate=gen_stats["success_rate"],
            total_deposits=revenue_stats["total_deposits"],
            today_deposits=revenue_stats["today_deposits"],
            week_deposits=revenue_stats["week_deposits"],
            month_deposits=revenue_stats["month_deposits"],
            total_refunded=revenue_stats.get("total_refunded", 0.0),
            total_spent=revenue_stats["total_spent"],
            net_revenue=revenue_stats["net_revenue"],
            by_model=revenue_stats.get("by_model", {}),
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


# ============ Chart Data ============


@router.get("/charts/users-daily")
async def get_users_daily(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get daily new user registrations for chart."""
    try:
        service = AdminService(session)
        data = await service.get_daily_users(days)
        return data
    except Exception as e:
        logger.exception("Failed to get daily users", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/generations-daily")
async def get_generations_daily(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get daily generation stats for chart."""
    try:
        service = AdminService(session)
        data = await service.get_daily_generations(days)
        return data
    except Exception as e:
        logger.exception("Failed to get daily generations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/revenue-daily")
async def get_revenue_daily(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get daily revenue stats for chart."""
    try:
        service = AdminService(session)
        data = await service.get_daily_revenue(days)
        return data
    except Exception as e:
        logger.exception("Failed to get daily revenue", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/models-breakdown")
async def get_models_breakdown(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get generation count and credits by model for chart."""
    try:
        service = AdminService(session)
        data = await service.get_models_breakdown(days)
        return data
    except Exception as e:
        logger.exception("Failed to get models breakdown", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============ User Management ============


@router.get("/users", response_model=UserListOut)
async def search_users(
    query: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
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

            result_users.append(
                AdminUserOut(
                    telegram_id=user.telegram_id,
                    username=None,
                    first_name=None,
                    last_name=None,
                    language_code="uz",
                    is_active=True,
                    is_banned=user.is_banned if hasattr(user, "is_banned") else False,
                    ban_reason=None,
                    trial_remaining=3,
                    balance=Decimal(balance),
                    referrer_id=user.referred_by_id,
                    referral_count=referral_count,
                    generation_count=gen_count,
                    created_at=user.created_at,
                    last_active_at=user.last_active_at if hasattr(user, "last_active_at") else None,
                )
            )

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


@router.get("/users/count")
async def get_users_count(
    filter_type: str = Query(default="all"),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get users count by filter for preview."""
    try:
        service = BroadcastService(session)
        count = await service.get_filtered_users_count(filter_type)
        return {"count": count, "filter_type": filter_type}
    except Exception as e:
        logger.exception("Failed to get users count", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/users/{telegram_id}", response_model=AdminUserOut)
async def get_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
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
            is_banned=user.is_banned if hasattr(user, "is_banned") else False,
            ban_reason=None,
            trial_remaining=3,
            balance=Decimal(balance),
            referrer_id=user.referred_by_id,
            referral_count=referral_count,
            generation_count=gen_count,
            created_at=user.created_at,
            last_active_at=user.last_active_at if hasattr(user, "last_active_at") else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/users/{telegram_id}/ban")
async def ban_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Ban a user."""
    try:
        service = AdminService(session)
        user = await service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_banned = True
        await session.commit()
        return {"success": True, "telegram_id": telegram_id, "is_banned": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to ban user", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{telegram_id}/unban")
async def unban_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Unban a user."""
    try:
        service = AdminService(session)
        user = await service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_banned = False
        await session.commit()
        return {"success": True, "telegram_id": telegram_id, "is_banned": False}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to unban user", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============ Credits Management ============


@router.post("/credits", response_model=AdminCreditOut)
async def adjust_credits(
    data: AdminCreditIn,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
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


# ============ User Generations ============


@router.get("/users/{telegram_id}/generations")
async def get_user_generations(
    telegram_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get user's recent generations."""
    try:
        service = AdminService(session)

        user = await service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        generations = await service.get_user_generations(user.id, limit)
        return generations
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get user generations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ Refund Generation ============


@router.post("/generations/{generation_id}/refund")
async def refund_generation(
    generation_id: int,
    data: dict,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Refund a specific generation."""
    try:
        telegram_id = data.get("telegram_id")
        if not telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id required")

        service = AdminService(session)

        user = await service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = await service.refund_generation(user.id, generation_id)

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("message", "Refund failed"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to refund generation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ User Payments ============


@router.get("/users/{telegram_id}/payments")
async def get_user_payments(
    telegram_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get user's payment history."""
    try:
        service = AdminService(session)

        user = await service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        payments = await service.get_user_payments(user.id, limit)
        return payments
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get user payments", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ Broadcast Management ============


@router.post("/broadcasts", response_model=BroadcastOut)
async def create_broadcast(
    data: BroadcastCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Create a new broadcast (not started yet)."""
    try:
        service = BroadcastService(session)
        broadcast = await service.create_broadcast(
            admin_id=data.admin_id,
            content_type=data.content_type,
            text=data.text,
            media_file_id=data.media_file_id,
            inline_button_text=data.inline_button_text,
            inline_button_url=data.inline_button_url,
            filter_type=data.filter_type,
            filter_params=data.filter_params,
        )
        return broadcast
    except Exception as e:
        logger.exception("Failed to create broadcast", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/broadcasts", response_model=BroadcastListOut)
async def list_broadcasts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """List all broadcasts (newest first)."""
    try:
        service = BroadcastService(session)
        broadcasts = await service.list_broadcasts(limit=limit, offset=offset)
        return BroadcastListOut(broadcasts=broadcasts, total=len(broadcasts))
    except Exception as e:
        logger.exception("Failed to list broadcasts", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/broadcasts/{public_id}", response_model=BroadcastStatusOut)
async def get_broadcast_status(
    public_id: str,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get broadcast status and progress."""
    try:
        service = BroadcastService(session)
        broadcast = await service.get_broadcast_by_public_id(public_id)

        if not broadcast:
            raise HTTPException(status_code=404, detail="Broadcast not found")

        total = broadcast.total_users or 0
        sent = broadcast.sent_count or 0
        progress = (sent / total * 100) if total > 0 else 0.0

        return BroadcastStatusOut(
            public_id=broadcast.public_id,
            status=broadcast.status.value,
            total_users=total,
            sent_count=sent,
            failed_count=broadcast.failed_count or 0,
            blocked_count=broadcast.blocked_count or 0,
            progress_percent=round(progress, 1),
            started_at=broadcast.started_at,
            completed_at=broadcast.completed_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get broadcast status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/broadcasts/{public_id}/start")
async def start_broadcast(
    public_id: str,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Start sending a broadcast."""
    try:
        service = BroadcastService(session)
        broadcast = await service.get_broadcast_by_public_id(public_id)

        if not broadcast:
            raise HTTPException(status_code=404, detail="Broadcast not found")

        if broadcast.status.value != "pending":
            raise HTTPException(status_code=400, detail=f"Broadcast is {broadcast.status.value}, cannot start")

        # Start broadcast via Celery
        from app.worker.tasks import start_broadcast_task

        start_broadcast_task.delay(broadcast.id)

        return {"status": "started", "public_id": public_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to start broadcast", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/broadcasts/{public_id}/cancel")
async def cancel_broadcast(
    public_id: str,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Cancel a running broadcast."""
    try:
        service = BroadcastService(session)
        broadcast = await service.get_broadcast_by_public_id(public_id)

        if not broadcast:
            raise HTTPException(status_code=404, detail="Broadcast not found")

        if broadcast.status.value not in ("pending", "running"):
            raise HTTPException(status_code=400, detail=f"Broadcast is {broadcast.status.value}, cannot cancel")

        await service.cancel_broadcast(broadcast.id)

        return {"status": "cancelled", "public_id": public_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to cancel broadcast", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ Model Management ============


@router.get("/models")
async def get_all_models(
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get all models with prices and generation counts."""
    try:
        service = AdminService(session)
        models = await service.get_all_models()
        return models
    except Exception as e:
        logger.exception("Failed to get models", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{model_id}")
async def update_model(
    model_id: int,
    data: dict,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Update model fields (is_active, name)."""
    try:
        service = AdminService(session)
        result = await service.update_model(model_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Model not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update model", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/models/{model_id}/price")
async def update_model_price(
    model_id: int,
    data: dict,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Update model price."""
    try:
        unit_price = data.get("unit_price")
        if unit_price is None:
            raise HTTPException(status_code=400, detail="unit_price required")

        service = AdminService(session)
        result = await service.update_model_price(model_id, int(unit_price))
        if not result:
            raise HTTPException(status_code=404, detail="Model not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update model price", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============ Global Payments ============


@router.get("/payments")
async def get_global_payments(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get all payments with pagination."""
    try:
        service = AdminService(session)
        items, total = await service.get_global_payments(offset=offset, limit=limit)
        return {"items": items, "total": total}
    except Exception as e:
        logger.exception("Failed to get payments", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/daily")
async def get_payment_daily_stats(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get daily payment statistics."""
    try:
        service = AdminService(session)
        data = await service.get_payment_daily_stats(days)
        return data
    except Exception as e:
        logger.exception("Failed to get payment daily stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============ Global Generations ============


@router.get("/generations")
async def get_global_generations(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get all generations with pagination and optional status filter."""
    try:
        service = AdminService(session)
        items, total = await service.get_global_generations(offset=offset, limit=limit, status_filter=status_filter)
        return {"items": items, "total": total}
    except Exception as e:
        logger.exception("Failed to get generations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generations/queue")
async def get_generation_queue(
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get current generation queue status."""
    try:
        service = AdminService(session)
        queue = await service.get_generation_queue_status()
        return queue
    except Exception as e:
        logger.exception("Failed to get queue status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============ System Settings ============


@router.get("/settings")
async def get_system_settings(
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Get all system settings."""
    try:
        from sqlalchemy import select as sa_select

        from app.db.models import SystemSetting

        result = await session.execute(sa_select(SystemSetting).order_by(SystemSetting.key))
        settings = result.scalars().all()
        return [
            {
                "key": s.key,
                "value": s.value,
                "value_type": s.value_type,
                "description": s.description,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in settings
        ]
    except Exception as e:
        logger.exception("Failed to get settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/settings")
async def update_system_settings(
    data: dict,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(require_admin),
):
    """Update system settings. Body: {key: value, key2: value2, ...}."""
    try:
        from datetime import datetime

        from sqlalchemy import select as sa_select

        from app.db.models import SystemSetting

        updated = []
        for key, value in data.items():
            result = await session.execute(sa_select(SystemSetting).where(SystemSetting.key == key))
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = str(value)
                setting.updated_by = admin["telegram_id"]
                setting.updated_at = datetime.utcnow()
                updated.append(key)

        await session.commit()
        return {"updated": updated, "count": len(updated)}
    except Exception as e:
        logger.exception("Failed to update settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
