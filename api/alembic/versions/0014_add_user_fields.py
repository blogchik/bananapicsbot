"""Add user profile fields.

Revision ID: 0014_add_user_fields
Revises: 0013_add_referrals
Create Date: 2024-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0014_add_user_fields"
down_revision: Union[str, None] = "0013_add_referrals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new user profile fields."""
    # Add username
    op.add_column(
        "users",
        sa.Column("username", sa.String(100), nullable=True),
    )
    
    # Add first_name
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(100), nullable=True),
    )
    
    # Add last_name
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(100), nullable=True),
    )
    
    # Add language_code with default
    op.add_column(
        "users",
        sa.Column("language_code", sa.String(10), nullable=False, server_default="uz"),
    )
    
    # Add is_banned
    op.add_column(
        "users",
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
    )
    
    # Add ban_reason
    op.add_column(
        "users",
        sa.Column("ban_reason", sa.Text(), nullable=True),
    )
    
    # Add is_admin
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )
    
    # Add is_active
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    
    # Add trial_remaining
    op.add_column(
        "users",
        sa.Column("trial_remaining", sa.Integer(), nullable=False, server_default="3"),
    )
    
    # Add updated_at
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    
    # Add last_active_at
    op.add_column(
        "users",
        sa.Column(
            "last_active_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove user profile fields."""
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "trial_remaining")
    op.drop_column("users", "is_active")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "ban_reason")
    op.drop_column("users", "is_banned")
    op.drop_column("users", "language_code")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "username")
