"""add referrals

Revision ID: 0013_add_referrals
Revises: 0012_expand_ledger_reference_id
Create Date: 2026-01-15 00:00:00.000000
"""

import secrets

import sqlalchemy as sa
from alembic import op

revision = "0013_add_referrals"
down_revision = "0012_expand_ledger_reference_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("referral_code", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("referred_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_referred_by_id",
        "users",
        "users",
        ["referred_by_id"],
        ["id"],
    )

    connection = op.get_bind()
    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("referral_code", sa.String),
    )
    existing_ids = connection.execute(sa.select(users_table.c.id)).fetchall()
    for row in existing_ids:
        code = secrets.token_hex(4)
        while connection.execute(
            sa.select(users_table.c.id).where(users_table.c.referral_code == code)
        ).scalar_one_or_none():
            code = secrets.token_hex(4)
        connection.execute(users_table.update().where(users_table.c.id == row.id).values(referral_code=code))

    op.alter_column("users", "referral_code", nullable=False)
    op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=True)
    op.create_index("ix_users_referred_by_id", "users", ["referred_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_referred_by_id", table_name="users")
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_constraint("fk_users_referred_by_id", "users", type_="foreignkey")
    op.drop_column("users", "referred_by_id")
    op.drop_column("users", "referral_code")
