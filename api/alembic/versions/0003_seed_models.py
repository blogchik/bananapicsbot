"""seed seedream-v4 model

Revision ID: 0003_seed_models
Revises: 0002_add_generation_models
Create Date: 2026-01-14 22:10:00.000000
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "0003_seed_models"
down_revision = "0002_add_generation_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    model_table = sa.table(
        "model_catalog",
        sa.column("id", sa.Integer),
        sa.column("key", sa.String),
        sa.column("name", sa.String),
        sa.column("provider", sa.String),
        sa.column("supports_reference", sa.Boolean),
        sa.column("supports_aspect_ratio", sa.Boolean),
        sa.column("supports_style", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )

    price_table = sa.table(
        "model_prices",
        sa.column("id", sa.Integer),
        sa.column("model_id", sa.Integer),
        sa.column("currency", sa.String),
        sa.column("unit_price", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )

    now = datetime.utcnow()

    op.bulk_insert(
        model_table,
        [
            {
                "key": "seedream-v4",
                "name": "Seedream v4",
                "provider": "seedream",
                "supports_reference": False,
                "supports_aspect_ratio": False,
                "supports_style": False,
                "is_active": True,
                "created_at": now,
            }
        ],
    )

    model_id = op.get_bind().execute(
        sa.text("SELECT id FROM model_catalog WHERE key = :key"),
        {"key": "seedream-v4"},
    ).scalar_one()

    op.bulk_insert(
        price_table,
        [
            {
                "model_id": model_id,
                "currency": "credit",
                "unit_price": 1,
                "is_active": True,
                "created_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM model_prices WHERE model_id IN (SELECT id FROM model_catalog WHERE key = 'seedream-v4')")
    op.execute("DELETE FROM model_catalog WHERE key = 'seedream-v4'")
