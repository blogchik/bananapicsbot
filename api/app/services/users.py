from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.services.referrals import generate_referral_code


def get_or_create_user(
    db: Session,
    telegram_id: int,
    referral_code: str | None = None,
) -> tuple[User, User | None, bool]:
    user = db.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalar_one_or_none()
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
        referrer = db.execute(
            select(User).where(User.referral_code == referral_code)
        ).scalar_one_or_none()
        if referrer and referrer.id != user.id:
            user.referred_by_id = referrer.id
            referral_applied = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, referrer, referral_applied


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return db.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalar_one_or_none()
