from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import LedgerEntry, User
from app.services.referrals import generate_referral_code


def get_or_create_user(
    db: Session,
    telegram_id: int,
    referral_code: str | None = None,
) -> tuple[User, User | None, bool]:
    user = db.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
    if user:
        if not user.referral_code:
            user.referral_code = generate_referral_code(db)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user, None, False
    user = User(telegram_id=telegram_id, referral_code=generate_referral_code(db))
    referrer = None
    referral_applied = False
    if referral_code:
        referrer = db.execute(select(User).where(User.referral_code == referral_code)).scalar_one_or_none()
        if referrer and referrer.id != user.id:
            user.referred_by_id = referrer.id
            referral_applied = True
    db.add(user)
    db.commit()
    db.refresh(user)

    # Award join bonus to referrer if referral was applied
    if referral_applied and referrer:
        settings = get_settings()
        join_bonus = settings.referral_join_bonus
        if join_bonus > 0:
            db.add(
                LedgerEntry(
                    user_id=referrer.id,
                    amount=join_bonus,
                    entry_type="referral_join_bonus",
                    reference_id=str(user.telegram_id),
                    description="Referral join bonus",
                )
            )
            db.commit()

    return user, referrer, referral_applied


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return db.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
