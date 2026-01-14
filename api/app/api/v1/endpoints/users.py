from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.schemas.balance import BalanceOut
from app.schemas.trial import TrialStatusOut
from app.schemas.user import UserBase, UserOut
from app.services.ledger import get_user_balance
from app.services.users import get_or_create_user, get_user_by_telegram_id

router = APIRouter()


@router.post("/users/sync", response_model=UserOut, status_code=status.HTTP_200_OK)
async def sync_user(payload: UserBase, db: Session = Depends(db_session_dep)) -> UserOut:
    user = get_or_create_user(db, payload.telegram_id)
    return UserOut.model_validate(user)


@router.get("/users/{telegram_id}/balance", response_model=BalanceOut)
async def get_balance(telegram_id: int, db: Session = Depends(db_session_dep)) -> BalanceOut:
    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    balance = get_user_balance(db, user.id)
    return BalanceOut(user_id=user.id, balance=balance)


@router.get("/users/{telegram_id}/trial", response_model=TrialStatusOut)
async def get_trial_status(telegram_id: int, db: Session = Depends(db_session_dep)) -> TrialStatusOut:
    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    used_count = len(user.trial_uses)
    return TrialStatusOut(
        user_id=user.id,
        trial_available=used_count == 0,
        used_count=used_count,
    )
