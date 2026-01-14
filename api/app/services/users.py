from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


def get_or_create_user(db: Session, telegram_id: int) -> User:
    user = db.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalar_one_or_none()
    if user:
        return user
    user = User(telegram_id=telegram_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return db.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalar_one_or_none()
