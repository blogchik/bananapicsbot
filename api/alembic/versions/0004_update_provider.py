"""update seedream provider to wavespeed

Revision ID: 0004_update_provider
Revises: 0003_seed_models
Create Date: 2026-01-14 22:18:00.000000
"""

from alembic import op

revision = "0004_update_provider"
down_revision = "0003_seed_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE model_catalog SET provider = 'wavespeed' WHERE key = 'seedream-v4'")


def downgrade() -> None:
    op.execute("UPDATE model_catalog SET provider = 'seedream' WHERE key = 'seedream-v4'")
