from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LedgerEntry


def get_user_balance(db: Session, user_id: int) -> int:
    stmt = select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(LedgerEntry.user_id == user_id)
    return int(db.execute(stmt).scalar_one())
