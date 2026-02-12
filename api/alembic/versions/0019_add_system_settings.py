"""add system settings

Revision ID: 0019_add_system_settings
Revises: 0018_add_qwen_model
Create Date: 2026-02-12 00:00:00.000000
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0019_add_system_settings"
down_revision = "0018_add_qwen_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, index=True, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(20), server_default="string", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed default settings
    settings_table = sa.table(
        "system_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("value_type", sa.String),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.DateTime),
    )

    now = datetime.utcnow()
    op.bulk_insert(
        settings_table,
        [
            {
                "key": "trial_generations_limit",
                "value": "3",
                "value_type": "int",
                "description": "Number of free trial generations per user",
                "created_at": now,
            },
            {
                "key": "stars_exchange_numerator",
                "value": "1",
                "value_type": "int",
                "description": "Stars exchange rate numerator (stars * numerator / denominator = credits)",
                "created_at": now,
            },
            {
                "key": "stars_exchange_denominator",
                "value": "1",
                "value_type": "int",
                "description": "Stars exchange rate denominator",
                "created_at": now,
            },
            {
                "key": "referral_bonus_percent",
                "value": "10",
                "value_type": "int",
                "description": "Referral bonus percentage for referrer when referee makes a purchase",
                "created_at": now,
            },
            {
                "key": "referral_join_bonus",
                "value": "0",
                "value_type": "int",
                "description": "Credits bonus for both referrer and referee on join",
                "created_at": now,
            },
            {
                "key": "max_parallel_generations_per_user",
                "value": "2",
                "value_type": "int",
                "description": "Maximum simultaneous generation requests per user",
                "created_at": now,
            },
            {
                "key": "generation_price_markup",
                "value": "0",
                "value_type": "int",
                "description": "Additional credits markup per generation (0 = no markup)",
                "created_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("system_settings")
