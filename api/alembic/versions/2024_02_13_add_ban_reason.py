"""Add ban_reason to users

Revision ID: 2024_02_13_ban_reason
Revises: 0020_add_more_settings
Create Date: 2024-02-13 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "2024_02_13_ban_reason"
down_revision: Union[str, None] = "0020_add_more_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("users")]

    if "ban_reason" not in columns:
        op.add_column("users", sa.Column("ban_reason", sa.String(500), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("users")]

    if "ban_reason" in columns:
        op.drop_column("users", "ban_reason")
