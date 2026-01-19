"""create payment ledger

Revision ID: 0011_create_payment_ledger
Revises: 0010_update_model_prices
Create Date: 2026-01-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0011_create_payment_ledger"
down_revision = "0010_update_model_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column("credits_amount", sa.Integer(), nullable=False),
        sa.Column("telegram_charge_id", sa.String(length=200), nullable=False),
        sa.Column("provider_charge_id", sa.String(length=200), nullable=True),
        sa.Column("invoice_payload", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_payment_ledger_user_id", "payment_ledger", ["user_id"], unique=False
    )
    op.create_index(
        "ix_payment_ledger_telegram_charge_id",
        "payment_ledger",
        ["telegram_charge_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_payment_ledger_telegram_charge_id", table_name="payment_ledger")
    op.drop_index("ix_payment_ledger_user_id", table_name="payment_ledger")
    op.drop_table("payment_ledger")
