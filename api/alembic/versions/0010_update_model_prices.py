"""update model prices

Revision ID: 0010_update_model_prices
Revises: 0009_add_nano_banana_models
Create Date: 2026-01-15 00:00:00.000000
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "0010_update_model_prices"
down_revision = "0009_add_nano_banana_models"
branch_labels = None
depends_on = None


MODEL_PRICES = {
    "seedream-v4": 27,
    "nano-banana": 38,
    "nano-banana-pro": 140,
}


def _apply_prices(conn, unit_prices: dict[str, int]) -> None:
    now = datetime.utcnow()
    for key, price in unit_prices.items():
        model_id = conn.execute(
            sa.text("SELECT id FROM model_catalog WHERE key = :key"),
            {"key": key},
        ).scalar_one_or_none()
        if not model_id:
            continue
        conn.execute(
            sa.text(
                """
                UPDATE model_prices
                SET is_active = false
                WHERE model_id = :model_id AND is_active = true
                """
            ),
            {"model_id": model_id},
        )
        conn.execute(
            sa.text(
                """
                INSERT INTO model_prices (
                    model_id,
                    currency,
                    unit_price,
                    is_active,
                    created_at
                )
                VALUES (:model_id, 'credit', :unit_price, true, :created_at)
                """
            ),
            {"model_id": model_id, "unit_price": price, "created_at": now},
        )


def upgrade() -> None:
    conn = op.get_bind()
    _apply_prices(conn, MODEL_PRICES)


def downgrade() -> None:
    conn = op.get_bind()
    default_prices = {key: 1 for key in MODEL_PRICES}
    _apply_prices(conn, default_prices)
