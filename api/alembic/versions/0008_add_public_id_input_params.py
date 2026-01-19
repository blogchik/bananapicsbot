"""add generation public id and input params

Revision ID: 0008_add_public_id_input_params
Revises: 0006_add_generation_size
Create Date: 2026-01-14 23:32:00.000000
"""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0008_add_public_id_input_params"
down_revision = "0006_add_generation_size"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_requests",
        sa.Column("public_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "generation_requests",
        sa.Column("input_params", sa.JSON(), nullable=True),
    )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM generation_requests WHERE public_id IS NULL"))
    for row in rows:
        conn.execute(
            sa.text("UPDATE generation_requests SET public_id = :pid WHERE id = :id"),
            {"pid": str(uuid.uuid4()), "id": row.id},
        )

    op.create_index(
        "ix_generation_requests_public_id",
        "generation_requests",
        ["public_id"],
        unique=True,
    )
    op.alter_column("generation_requests", "public_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_generation_requests_public_id", table_name="generation_requests")
    op.drop_column("generation_requests", "input_params")
    op.drop_column("generation_requests", "public_id")
