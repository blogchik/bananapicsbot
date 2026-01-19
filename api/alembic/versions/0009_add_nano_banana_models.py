"""add nano banana models

Revision ID: 0009_add_nano_banana_models
Revises: 0008_add_public_id_input_params
Create Date: 2026-01-15 00:30:00.000000
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0009_add_nano_banana_models"
down_revision = "0008_add_public_id_input_params"
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = datetime.utcnow()
    conn = op.get_bind()

    models = [
        {
            "key": "nano-banana",
            "name": "Nano Banana",
        },
        {
            "key": "nano-banana-pro",
            "name": "Nano Banana Pro",
        },
    ]

    for model in models:
        conn.execute(
            sa.text(
                """
                INSERT INTO model_catalog (
                    key,
                    name,
                    provider,
                    supports_reference,
                    supports_aspect_ratio,
                    supports_style,
                    supports_text_to_image,
                    supports_image_to_image,
                    is_active,
                    created_at
                )
                VALUES (
                    :key,
                    :name,
                    'wavespeed',
                    true,
                    true,
                    false,
                    true,
                    true,
                    true,
                    :created_at
                )
                ON CONFLICT (key) DO NOTHING
                """
            ),
            {"key": model["key"], "name": model["name"], "created_at": now},
        )

        conn.execute(
            sa.text(
                """
                UPDATE model_catalog
                SET supports_reference = true,
                    supports_aspect_ratio = true,
                    supports_style = false,
                    supports_text_to_image = true,
                    supports_image_to_image = true,
                    is_active = true
                WHERE key = :key
                """
            ),
            {"key": model["key"]},
        )

        model_id = conn.execute(
            sa.text("SELECT id FROM model_catalog WHERE key = :key"),
            {"key": model["key"]},
        ).scalar_one()

        existing_price = conn.execute(
            sa.text(
                """
                SELECT id FROM model_prices
                WHERE model_id = :model_id AND is_active = true
                """
            ),
            {"model_id": model_id},
        ).scalar_one_or_none()

        if existing_price is None:
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
                    VALUES (:model_id, 'credit', 1, true, :created_at)
                    """
                ),
                {"model_id": model_id, "created_at": now},
            )


def downgrade() -> None:
    op.execute(
        "DELETE FROM model_prices WHERE model_id IN (SELECT id FROM model_catalog WHERE key IN ('nano-banana', 'nano-banana-pro'))"
    )
    op.execute(
        "DELETE FROM model_catalog WHERE key IN ('nano-banana', 'nano-banana-pro')"
    )
