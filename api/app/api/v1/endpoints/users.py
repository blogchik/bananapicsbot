from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.deps.db import db_session_dep
from app.deps.telegram_auth import TelegramUserDep
from app.schemas.balance import BalanceOut
from app.schemas.trial import TrialStatusOut
from app.schemas.user import UserSyncIn, UserSyncOut
from app.services.ledger import get_user_balance
from app.services.users import get_or_create_user, get_user_by_telegram_id

router = APIRouter()


@router.post("/users/sync", response_model=UserSyncOut, status_code=status.HTTP_200_OK)
async def sync_user(
    payload: UserSyncIn,
    tg_user: TelegramUserDep,
    db: Session = Depends(db_session_dep),
) -> UserSyncOut:
    """
    Sync user from Telegram to database.
    Creates user if not exists, applies referral if provided.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only sync their own data
    if payload.telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot sync data for another user",
        )

    referral_code = payload.referral_code or ""
    if referral_code.startswith("r_"):
        referral_code = referral_code[2:]
    referral_code = referral_code.strip() or None

    user, referrer, referral_applied = get_or_create_user(
        db,
        payload.telegram_id,
        referral_code,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        language_code=payload.language_code,
    )
    settings = get_settings()
    return UserSyncOut(
        id=user.id,
        telegram_id=user.telegram_id,
        created_at=user.created_at,
        referral_code=user.referral_code,
        referral_applied=referral_applied,
        referrer_telegram_id=referrer.telegram_id if referral_applied and referrer else None,
        bonus_percent=settings.referral_bonus_percent,
    )


@router.get("/users/{telegram_id}/balance", response_model=BalanceOut)
async def get_balance(
    telegram_id: int,
    tg_user: TelegramUserDep,
    db: Session = Depends(db_session_dep),
) -> BalanceOut:
    """
    Get user balance.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only access their own balance
    if telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access balance for another user",
        )

    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    balance = get_user_balance(db, user.id)
    return BalanceOut(user_id=user.id, balance=balance)


@router.get("/users/{telegram_id}/trial", response_model=TrialStatusOut)
async def get_trial_status(
    telegram_id: int,
    tg_user: TelegramUserDep,
    db: Session = Depends(db_session_dep),
) -> TrialStatusOut:
    """
    Get user trial status.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only access their own trial status
    if telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access trial status for another user",
        )

    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    used_count = len(user.trial_uses)
    return TrialStatusOut(
        user_id=user.id,
        trial_available=used_count == 0,
        used_count=used_count,
    )
