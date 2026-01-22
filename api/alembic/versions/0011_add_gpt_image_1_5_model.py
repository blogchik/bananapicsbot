"""add gpt image 1.5 model

Revision ID: 0011_add_gpt_image_1_5_model
Revises: 0010_update_model_prices
Create Date: 2026-01-18 00:00:00.000000
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0011_add_gpt_image_1_5_model"
down_revision = "0010_update_model_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = datetime.utcnow()
    conn = op.get_bind()

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
                'gpt-image-1.5',
                'GPT Image 1.5',
                'wavespeed',
                true,
                false,
                false,
                true,
                true,
                true,
                :created_at
            )
            ON CONFLICT (key) DO NOTHING
            """
        ),
        {"created_at": now},
    )

    conn.execute(
        sa.text(
            """
            UPDATE model_catalog
            SET supports_reference = true,
                supports_aspect_ratio = false,
                supports_style = false,
                supports_text_to_image = true,
                supports_image_to_image = true,
                is_active = true
            WHERE key = 'gpt-image-1.5'
            """
        )
    )

    model_id = conn.execute(sa.text("SELECT id FROM model_catalog WHERE key = 'gpt-image-1.5'")).scalar_one()

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
                VALUES (:model_id, 'credit', 40, true, :created_at)
                """
            ),
            {"model_id": model_id, "created_at": now},
        )


def downgrade() -> None:
    op.execute("DELETE FROM model_prices WHERE model_id IN (SELECT id FROM model_catalog WHERE key = 'gpt-image-1.5')")
    op.execute("DELETE FROM model_catalog WHERE key = 'gpt-image-1.5'")
