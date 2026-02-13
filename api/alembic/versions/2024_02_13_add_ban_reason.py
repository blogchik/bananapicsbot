"""Add ban_reason to users

Revision ID: 2024_02_13_ban_reason
Revises:
Create Date: 2024-02-13 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2024_02_13_ban_reason"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ban_reason", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ban_reason")
