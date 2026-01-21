"""add qwen model

Revision ID: 0018_add_qwen_model
Revises: 0017_add_is_refunded
Create Date: 2026-01-21 00:00:00.000000
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0018_add_qwen_model"
down_revision = "0017_add_is_refunded"
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = datetime.utcnow()
    conn = op.get_bind()

    # Insert qwen model
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
                'qwen',
                'QWEN Image',
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

    # Update flags if already exists
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
            WHERE key = 'qwen'
            """
        )
    )

    # Get model ID
    model_id = conn.execute(
        sa.text("SELECT id FROM model_catalog WHERE key = 'qwen'")
    ).scalar_one()

    # Check if price already exists
    existing_price = conn.execute(
        sa.text(
            """
            SELECT id FROM model_prices
            WHERE model_id = :model_id AND is_active = true
            """
        ),
        {"model_id": model_id},
    ).scalar_one_or_none()

    # Insert price if not exists ($0.02 per image = ~20 credits)
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
                VALUES (:model_id, 'credit', 20, true, :created_at)
                """
            ),
            {"model_id": model_id, "created_at": now},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM model_prices WHERE model_id IN "
            "(SELECT id FROM model_catalog WHERE key = 'qwen')"
        )
    )
    conn.execute(
        sa.text("DELETE FROM model_catalog WHERE key = 'qwen'")
    )
