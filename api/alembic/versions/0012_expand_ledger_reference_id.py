"""expand ledger reference id

Revision ID: 0012_expand_ledger_reference_id
Revises: 0011_create_payment_ledger
Create Date: 2026-01-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_expand_ledger_reference_id"
down_revision = "0011_create_payment_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ledger_entries",
        "reference_id",
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "ledger_entries",
        "reference_id",
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
