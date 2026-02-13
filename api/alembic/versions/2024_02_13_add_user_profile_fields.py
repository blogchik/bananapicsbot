"""Add user profile fields

Revision ID: 2024_02_13_profile
Revises:
Create Date: 2024-02-13 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2024_02_13_profile"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column("users", sa.Column("username", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("first_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("photo_url", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("language_code", sa.String(10), nullable=True, server_default="uz"))
    op.add_column("users", sa.Column("ban_reason", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("trial_remaining", sa.Integer(), nullable=True, server_default="3"))


def downgrade() -> None:
    op.drop_column("users", "trial_remaining")
    op.drop_column("users", "ban_reason")
    op.drop_column("users", "language_code")
    op.drop_column("users", "photo_url")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "username")
