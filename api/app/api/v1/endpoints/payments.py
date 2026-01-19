from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import LedgerEntry, PaymentLedger
from app.deps.db import db_session_dep
from app.schemas.payments import (
    StarsPaymentConfirmIn,
    StarsPaymentConfirmOut,
    StarsPaymentOptionsOut,
)
from app.services.ledger import get_user_balance
from app.services.payments import calculate_credits, get_stars_settings
from app.services.referrals import calculate_referral_bonus
from app.services.users import get_or_create_user

router = APIRouter()


@router.get("/payments/stars/options", response_model=StarsPaymentOptionsOut)
async def get_stars_options() -> StarsPaymentOptionsOut:
    settings = get_stars_settings()
    return StarsPaymentOptionsOut(
        enabled=bool(settings["enabled"]),
        min_stars=int(settings["min_stars"]),
        preset_stars=list(settings["presets"]),
        exchange_numerator=int(settings["numerator"]),
        exchange_denominator=int(settings["denominator"]),
        currency=str(settings["currency"]),
    )


@router.post("/payments/stars/confirm", response_model=StarsPaymentConfirmOut)
async def confirm_stars_payment(
    payload: StarsPaymentConfirmIn,
    db: Session = Depends(db_session_dep),
) -> StarsPaymentConfirmOut:
    settings = get_stars_settings()
    if not settings["enabled"]:
        raise HTTPException(status_code=403, detail="Stars payments are disabled")
    min_stars = int(settings["min_stars"])
    currency = str(settings["currency"])
    if payload.currency != currency:
        raise HTTPException(status_code=400, detail="Invalid currency")
    if payload.stars_amount < min_stars:
        raise HTTPException(status_code=400, detail="Stars amount below minimum")

    existing = db.execute(
        select(PaymentLedger).where(
            PaymentLedger.telegram_charge_id == payload.telegram_charge_id
        )
    ).scalar_one_or_none()
    if existing:
        balance = get_user_balance(db, existing.user_id)
        return StarsPaymentConfirmOut(
            credits_added=existing.credits_amount,
            balance=balance,
        )

    user, _, _ = get_or_create_user(db, payload.telegram_id)
    credits = calculate_credits(
        payload.stars_amount,
        int(settings["numerator"]),
        int(settings["denominator"]),
    )
    if credits <= 0:
        raise HTTPException(status_code=400, detail="Invalid credit amount")

    payment = PaymentLedger(
        user_id=user.id,
        provider="telegram-stars",
        currency=payload.currency,
        stars_amount=payload.stars_amount,
        credits_amount=credits,
        telegram_charge_id=payload.telegram_charge_id,
        provider_charge_id=payload.provider_charge_id,
        invoice_payload=payload.invoice_payload,
    )
    db.add(payment)
    db.add(
        LedgerEntry(
            user_id=user.id,
            amount=credits,
            entry_type="topup_stars",
            reference_id=payload.telegram_charge_id,
            description="Telegram Stars topup",
        )
    )
    if user.referred_by_id:
        settings = get_settings()
        bonus = calculate_referral_bonus(credits, settings.referral_bonus_percent)
        if bonus > 0:
            db.add(
                LedgerEntry(
                    user_id=user.referred_by_id,
                    amount=bonus,
                    entry_type="referral_bonus",
                    reference_id=payload.telegram_charge_id,
                    description="Referral bonus",
                )
            )
    db.commit()

    balance = get_user_balance(db, user.id)
    return StarsPaymentConfirmOut(credits_added=credits, balance=balance)
