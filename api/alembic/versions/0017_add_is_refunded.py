"""Add is_refunded to payment_ledger.

Revision ID: 0017
Revises: 0016_add_generation_indexes
Create Date: 2026-01-19

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0017_add_is_refunded"
down_revision = "0016_add_generation_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_ledger",
        sa.Column(
            "is_refunded",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("payment_ledger", "is_refunded")
