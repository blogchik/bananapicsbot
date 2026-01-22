"""create broadcasts table

Revision ID: 0015
Revises: 0014
Create Date: 2026-01-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0015_create_broadcasts"
down_revision: Union[str, None] = "0014_add_user_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create broadcast_status enum first
    broadcast_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "cancelled", "failed", name="broadcast_status", create_type=False
    )
    op.execute("CREATE TYPE broadcast_status AS ENUM ('pending', 'running', 'completed', 'cancelled', 'failed')")

    # Create broadcasts table
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("media_file_id", sa.String(200), nullable=True),
        sa.Column("inline_button_text", sa.String(100), nullable=True),
        sa.Column("inline_button_url", sa.String(500), nullable=True),
        sa.Column(
            "filter_type",
            sa.String(50),
            nullable=False,
            server_default="all",
        ),
        sa.Column("filter_params", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            broadcast_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total_users", sa.Integer(), server_default="0"),
        sa.Column("sent_count", sa.Integer(), server_default="0"),
        sa.Column("failed_count", sa.Integer(), server_default="0"),
        sa.Column("blocked_count", sa.Integer(), server_default="0"),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_broadcasts_public_id", "broadcasts", ["public_id"], unique=True)
    op.create_index("ix_broadcasts_status", "broadcasts", ["status"])
    op.create_index("ix_broadcasts_admin_id", "broadcasts", ["admin_id"])

    # Create broadcast_recipients table for tracking individual sends
    op.create_table(
        "broadcast_recipients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("broadcast_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["broadcast_id"], ["broadcasts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_broadcast_recipients_broadcast_id", "broadcast_recipients", ["broadcast_id"])
    op.create_index("ix_broadcast_recipients_status", "broadcast_recipients", ["status"])


def downgrade() -> None:
    op.drop_table("broadcast_recipients")
    op.drop_table("broadcasts")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS broadcast_status")
