"""add size to generation requests

Revision ID: 0006_add_generation_size
Revises: 0005_add_model_types
Create Date: 2026-01-14 22:40:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_add_generation_size"
down_revision = "0005_add_model_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_requests",
        sa.Column("size", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generation_requests", "size")
