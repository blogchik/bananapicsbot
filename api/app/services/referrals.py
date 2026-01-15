import math
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LedgerEntry, User


def generate_referral_code(db: Session) -> str:
    for _ in range(5):
        code = secrets.token_hex(4)
        exists = db.execute(
            select(User.id).where(User.referral_code == code)
        ).scalar_one_or_none()
        if not exists:
            return code
    while True:
        code = secrets.token_hex(6)
        exists = db.execute(
            select(User.id).where(User.referral_code == code)
        ).scalar_one_or_none()
        if not exists:
            return code


def apply_referral(db: Session, user: User, referral_code: str | None) -> User | None:
    if not referral_code or user.referred_by_id:
        return None
    referrer = db.execute(
        select(User).where(User.referral_code == referral_code)
    ).scalar_one_or_none()
    if not referrer or referrer.id == user.id:
        return None
    user.referred_by_id = referrer.id
    db.add(user)
    db.commit()
    db.refresh(user)
    return referrer


def calculate_referral_bonus(credits: int, percent: int) -> int:
    if credits <= 0 or percent <= 0:
        return 0
    return int(math.ceil(credits * percent / 100))


def get_referral_stats(db: Session, user_id: int) -> tuple[int, int]:
    referrals_count = db.execute(
        select(func.count(User.id)).where(User.referred_by_id == user_id)
    ).scalar_one()
    total_bonus = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.user_id == user_id,
            LedgerEntry.entry_type == "referral_bonus",
        )
    ).scalar_one()
    return int(referrals_count), int(total_bonus)
