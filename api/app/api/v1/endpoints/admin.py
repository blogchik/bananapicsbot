from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.db.models import LedgerEntry
from app.schemas.admin import AdminCreditIn, AdminCreditOut
from app.services.ledger import get_user_balance
from app.services.users import get_or_create_user

router = APIRouter()


@router.post("/admin/credits/add", response_model=AdminCreditOut, status_code=status.HTTP_200_OK)
async def add_credits(
    payload: AdminCreditIn, db: Session = Depends(db_session_dep)
) -> AdminCreditOut:
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    description = payload.description or "Admin credit"
    db.add(
        LedgerEntry(
            user_id=user.id,
            amount=payload.credits,
            entry_type="admin_credit",
            description=description,
        )
    )
    db.commit()
    balance = get_user_balance(db, user.id)
    return AdminCreditOut(
        user_id=user.id,
        credits_added=payload.credits,
        balance=balance,
    )
