from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.core.config import get_settings
from app.schemas.referrals import ReferralInfoOut
from app.services.referrals import get_referral_stats
from app.services.users import get_user_by_telegram_id

router = APIRouter()


@router.get("/referrals/{telegram_id}", response_model=ReferralInfoOut)
async def get_referral_info(
    telegram_id: int, db: Session = Depends(db_session_dep)
) -> ReferralInfoOut:
    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    referrals_count, total_bonus = get_referral_stats(db, user.id)
    settings = get_settings()
    return ReferralInfoOut(
        user_id=user.id,
        referral_code=user.referral_code,
        referrals_count=referrals_count,
        referral_credits_total=total_bonus,
        bonus_percent=settings.referral_bonus_percent,
    )
