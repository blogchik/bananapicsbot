from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelCatalog, ModelPrice


def list_active_models(db: Session) -> list[ModelCatalog]:
    return db.execute(select(ModelCatalog).where(ModelCatalog.is_active.is_(True))).scalars().all()


def list_active_prices_for_models(db: Session, model_ids: list[int]) -> dict[int, list[ModelPrice]]:
    if not model_ids:
        return {}
    prices = (
        db.execute(
            select(ModelPrice).where(
                ModelPrice.model_id.in_(model_ids),
                ModelPrice.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )
    grouped: dict[int, list[ModelPrice]] = {}
    for price in prices:
        grouped.setdefault(price.model_id, []).append(price)
    return grouped
